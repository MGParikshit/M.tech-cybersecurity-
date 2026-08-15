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
