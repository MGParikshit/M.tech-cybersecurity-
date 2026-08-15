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

