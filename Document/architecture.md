<h1 align="center">🛡️ Malware Detection — System Architecture</h1>

<p align="center">
  <b>CNN-based static malware classification from raw PE byte images</b><br/>
  <sub>Two-part architecture: Model Training Pipeline + Frontend/Backend Serving Layer</sub>
</p>

---

## 📌 Overview

<table>
<tr>
<td><b>Problem</b></td>
<td>Signature-based malware detection fails against new or modified malware variants. This system uses a CNN trained on raw PE byte images to generalize to unseen threats.</td>
</tr>
<tr>
<td><b>Approach</b></td>
<td>Each PE file's raw byte stream is rescaled (nearest-neighbor interpolation) into a 32×32 grayscale image (1024 bytes flattened). A CNN classifies the image as <code>malware</code> or <code>benign</code>.</td>
</tr>
<tr>
<td><b>Dataset</b></td>
<td>51,959 samples × 1024 pixel columns + hash + label. Malware sourced from VirusShare; goodware from PortableApps and Windows 7 x86 system directories.</td>
</tr>
</table>

---

## 🧩 System at a Glance

```mermaid
flowchart LR
    subgraph P1["Part 1 — Model Training (Offline)"]
        direction TB
        A1[raw_pe_images.csv] --> A2[Preprocess & Normalize] --> A3[Train CNN] --> A4[malware_cnn_model.keras]
    end

    subgraph P2["Part 2 — Serving (Online)"]
        direction TB
        B1[User uploads .exe] --> B2[Frontend: bytes → 32x32 grayscale] --> B3[Backend API] --> B4[Loaded CNN Model] --> B5[Prediction + Threshold] --> B6[Result UI]
    end

    A4 -.deployed into.-> B4
```

---

## Part 1 — ML Model Training Pipeline

### 1.1 Data Pipeline

```mermaid
flowchart TD
    A[Load CSV\nraw_pe_images.csv] --> B[Inspect Dataset\nshape, columns, samples]
    B --> C[Split Columns\nX = pix_0...pix_1023\nY = malware label]
    C --> D[Normalize\nX = X / 255.0]
    D --> E[Reshape\nX → -1, 32, 32, 1]
    E --> F[Train/Test Split\n80% / 20%, random_state=42]
    F --> G[Detect GPU/CPU]
    G --> H[Build CNN Model]
```

<details>
<summary><b>📄 Dataset schema</b> (click to expand)</summary>

| Column(s) | Description |
|---|---|
| `hash` | Unique file identifier (dropped before training) |
| `pix_0` … `pix_1023` | Grayscale pixel values (0–255), flattened 32×32 image of the PE byte stream |
| `malware` | Label — `1` = malware, `0` = benign |

**Shape:** `(51959, 1026)` → `X: (51959, 1024)`, `Y: (51959,)`

</details>

### 1.2 CNN Architecture

```mermaid
flowchart TD
    IN["Input\n(32, 32, 1)"] --> C1["Conv2D\n32 filters, 3x3, ReLU"]
    C1 --> P1["MaxPooling2D\n2x2 → (16,16,32)"]
    P1 --> C2["Conv2D\n64 filters, 3x3, ReLU"]
    C2 --> P2["MaxPooling2D\n2x2 → (8,8,64)"]
    P2 --> FL["Flatten\n→ 4096"]
    FL --> D1["Dense\n64 units, ReLU"]
    D1 --> DO["Dropout\n0.5"]
    DO --> D2["Dense\n1 unit, Sigmoid"]
    D2 --> OUT["Output\nP(malware), 0–1"]
```

<table>
<thead>
<tr><th>Layer</th><th>Output Shape</th><th>Params</th></tr>
</thead>
<tbody>
<tr><td>Conv2D (32, 3x3)</td><td>(None, 32, 32, 32)</td><td>320</td></tr>
<tr><td>MaxPooling2D (2x2)</td><td>(None, 16, 16, 32)</td><td>0</td></tr>
<tr><td>Conv2D (64, 3x3)</td><td>(None, 16, 16, 64)</td><td>18,496</td></tr>
<tr><td>MaxPooling2D (2x2)</td><td>(None, 8, 8, 64)</td><td>0</td></tr>
<tr><td>Flatten</td><td>(None, 4096)</td><td>0</td></tr>
<tr><td>Dense (64, ReLU)</td><td>(None, 64)</td><td>262,208</td></tr>
<tr><td>Dropout (0.5)</td><td>(None, 64)</td><td>0</td></tr>
<tr><td>Dense (1, Sigmoid)</td><td>(None, 1)</td><td>65</td></tr>
</tbody>
</table>

**Total params:** 281,089 (1.07 MB) &nbsp;|&nbsp; **Optimizer:** Adam &nbsp;|&nbsp; **Loss:** Binary Crossentropy &nbsp;|&nbsp; **Epochs:** 100 &nbsp;|&nbsp; **Batch size:** 32

### 1.3 Training → Evaluation → Export

```mermaid
sequenceDiagram
    participant D as Dataset
    participant M as CNN Model
    participant F as Filesystem

    D->>M: fit(X_train, Y_train, epochs=100, val=(X_test,Y_test))
    M-->>M: accuracy: ~0.997 (train) / ~0.952 (val)
    M->>M: evaluate(X_test, Y_test)
    Note over M: Val Accuracy ≈ 95.2%
    M->>M: predict(sample) → prob ≥ 0.5 → label=1 (malware)
    M->>F: model.save("malware_cnn_model.keras")
```

> ⚠️ **Observation:** training accuracy climbs to ~99.7% while validation loss rises steadily after ~epoch 15–20 (val_loss 0.14 → 1.2+). This is classic **overfitting** — worth addressing with early stopping, L2 regularization, or data augmentation before production deployment.

---

## Part 2 — Frontend + Backend Serving Architecture

### 2.1 End-to-End Request Flow

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant FE as Frontend (React/Next.js)
    participant BE as Backend API (FastAPI/Flask)
    participant M as CNN Model (.keras)

    U->>FE: Upload .exe / .dll file
    FE->>FE: Read raw bytes
    FE->>FE: Convert byte stream → 32x32 grayscale (1024 values)
    FE->>BE: POST /predict {pixels: [1024 ints], filename, hash}
    BE->>BE: Validate payload, reshape (1,32,32,1)
    BE->>BE: Normalize: pixels / 255.0
    BE->>M: model.predict(input)
    M-->>BE: probability (0–1)
    BE->>BE: threshold ≥ 0.5 → "Malware" else "Benign"
    BE-->>FE: {label, confidence, hash}
    FE-->>U: Render result (Safe / Malicious + confidence)
```

### 2.2 Component Architecture

```mermaid
flowchart TB
    subgraph Client["🖥️ Frontend"]
        UP[Drag & Drop Upload Zone]
        CONV[Byte → Grayscale Converter]
        LOAD[Scanning / Loading State]
        RES[Results Dashboard]
    end

    subgraph Server["⚙️ Backend API"]
        EP[/POST /predict/]
        PRE[Preprocessing\nnormalize + reshape]
        MDL[(CNN Model\n.keras)]
        THR[Threshold Logic\n>=0.5 → Malware]
    end

    UP --> CONV --> EP
    EP --> PRE --> MDL --> THR --> RES
    LOAD -.shown during.-> EP
```

### 2.3 ⚖️ Design Decision — Byte Extraction / Resizing Strategy

The notebook's dataset description says the original pipeline used **nearest-neighbor interpolation over the entire PE byte stream**, not a simple truncation to the first 1024 bytes. This matters for inference-time consistency:

<table>
<tr>
<th>Option</th><th>Approach</th><th>Recommendation</th>
</tr>
<tr>
<td><b>A. Truncate/Pad</b></td>
<td>Take first 1024 bytes, zero-pad if file is shorter</td>
<td>❌ Simple but diverges from training distribution — headers-only bias</td>
</tr>
<tr>
<td><b>B. Nearest-Neighbor Resize (Recommended)</b></td>
<td>Read full file bytes → reshape to a square-ish 2D array → resize to 32×32 using nearest-neighbor (matches how the training set — <code>raw_pe_images.csv</code> — was generated per its documented methodology)</td>
<td>✅ Matches training-time distribution, keeps model calibration valid</td>
</tr>
</table>

> Whichever is chosen, use the **identical algorithm client-side (or server-side) that generated the training CSV** — a mismatch here is the single most common cause of silent accuracy degradation between offline eval and production.

### 2.4 Prediction → UI Mapping

```mermaid
flowchart LR
    P[Model Output\n0.0 - 1.0] --> Q{Score >= 0.5?}
    Q -->|Yes| M["🔴 Malware Detected\nRed warning UI + confidence %"]
    Q -->|No| S["🟢 File is Safe\nGreen success UI"]
```

---

## 🎨 Frontend Design Spec

<table>
<tr><td><b>Stack</b></td><td>React.js / Next.js · Tailwind CSS · FastAPI (Python) backend</td></tr>
<tr><td><b>Theme</b></td><td>Dark mode default (<code>#0f172a</code>) — cybersecurity aesthetic</td></tr>
<tr><td><b>Accent colors</b></td><td>🟢 <code>#10b981</code> safe · 🔴 <code>#ef4444</code> threat</td></tr>
<tr><td><b>Typography</b></td><td>Inter / Roboto, clean sans-serif</td></tr>
</table>

<details>
<summary><b>🧱 UI Components checklist</b></summary>

- [ ] Hero section — title + short description
- [ ] Drag & drop upload zone with hover/pulse micro-animations
- [ ] Radar-sweep / progress-bar loading state during backend processing
- [ ] Results dashboard:
  - Status badge (checkmark = safe, shield/warning = malware)
  - Circular confidence-score progress ring
  - File hash (MD5/SHA-256) + file size for an analytical feel

</details>

---

## 📂 Deployment Summary

```mermaid
flowchart LR
    NB[Training Notebook] -->|model.save| KM[malware_cnn_model.keras]
    KM --> API[FastAPI /predict endpoint]
    API --> WEB[React/Next.js Frontend]
    WEB --> END[End User Browser]
```
