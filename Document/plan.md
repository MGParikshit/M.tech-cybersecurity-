## Step 1: Frontend Implementation Plan

To build a frontend that works with this model, the architecture should consist of a **Web Client** (Frontend) and an **API Backend** (Model Serving layer).

### High-Level Workflow

1. **User Action**: The user uploads a PE file (e.g., `.exe`, `.dll`) or a converted 32x32 image via the frontend.
2. **Frontend Processing**: The frontend sends the file to the backend via a REST API or extracts the file bytes locally via JavaScript.
3. **Backend/Model Layer**: If a raw PE file is sent, the backend processes the first 1,024 bytes (or applies the specific PE-to-Image mapping algorithm) to create the 32x32 pixel array. It then normalizes the array (divide by 255) and passes it to the CNN model.
4. **Response**: The model returns a classification score, which the backend sends to the frontend.
5. **Display**: The frontend displays a rich, visual result indicating whether the file is "Safe" or "Malicious".

---

## Step 2: What is the Input Data & Where to Find It?

### What to give to the Frontend?

You can design the frontend to accept two types of inputs:

1. **Raw PE File Upload (Recommended)**: The user uploads an actual executable file (`.exe`). This is the most user-friendly approach. The backend will need a script to extract the bytes and convert them into the 1,024 pixel array.
2. **Image/CSV Row Upload**: The user uploads a 32x32 image or a JSON/CSV snippet containing the 1,024 pixel values directly.

### Where to find it?

- For testing the frontend, you can use the rows inside the `Dataset/raw_pe_images.csv` file. You can extract the 1,024 pixel values of a specific hash and pass them as a JSON payload to your backend.
- For real-world usage, users will provide their own PE files.

### The Procedure (Data Transformation Pipeline)

If accepting raw PE files:

1. Read the binary data of the file.
2. Convert the 8-bit binary data into decimal values (0-255).
3. Extract or sample exactly 1,024 values using the exact logic used to create the original dataset.
4. Reshape this into a `(32, 32, 1)` matrix.
5. Normalize the matrix by dividing by `255.0`.

---

## Step 3: What is the Output?

The model outputs a floating-point number between 0 and 1.

- **Frontend Output Mapping**:
  - `Score >= 0.5`: Display **"Malware Detected"** with a red warning interface, potentially showing the confidence percentage (e.g., `98% Confidence`).
  - `Score < 0.5`: Display **"File is Safe"** with a green success interface.

---

## Step 4: Frontend Design Plan

### Technology Stack

- **Framework**: React.js, Next.js, or Vanilla JS/HTML/CSS depending on your preference.
- **Styling**: Tailwind CSS or Vanilla CSS for a modern, glassmorphism aesthetic.
- **Backend API**: Python (FastAPI or Flask) to load the `.h5` / `.keras` model and serve predictions.

### User Interface (UI) Components

1. **Hero Section**:
   - A modern header with the title "AI Malware Scanner".
   - A brief description of the tool.
2. **Drag & Drop Upload Zone**:
   - A large, dashed-border area where users can drag and drop `.exe` files or click to browse.
   - Micro-animations (e.g., hover effects, pulse animations) to make the upload zone feel dynamic.
3. **Loading / Processing State**:
   - A scanning animation (e.g., a radar sweep or a progress bar) that displays while the backend processes the file.
4. **Results Dashboard**:
   - **Status Badge**: A prominent icon (Checkmark for Safe, Shield/Warning for Malware).
   - **Confidence Score**: A circular progress ring showing the model's confidence percentage.
   - **File Details**: Display the file hash (MD5/SHA256) and file size to add a professional, analytical feel.

### Aesthetics & Vibe

- **Theme**: Dark mode by default (e.g., `#0f172a` background) to fit the cybersecurity theme.
- **Colors**: Neon greens (`#10b981`) for safe files, and vibrant reds/oranges (`#ef4444`) for threats.
- **Typography**: Clean, modern sans-serif like `Inter` or `Roboto`.
