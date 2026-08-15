
# Part 2 — Frontend + Backend Serving Architecture

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
