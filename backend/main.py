from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from keras.models import load_model
from keras.layers import Dense

_original_dense_init = Dense.__init__

def _patched_dense_init(self, *args, **kwargs):
    kwargs.pop("quantization_config", None)
    _original_dense_init(self, *args, **kwargs)

Dense.__init__ = _patched_dense_init
import numpy as np
import hashlib
import json
import os


# ---------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------

app = FastAPI(
    title="Malware Detection API",
    description="CNN-based PE malware detection API",
    version="1.0.0"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Model
# ---------------------------------------------------------

MODEL_PATH = "malware_cnn_model.keras"

try:
    model = load_model(MODEL_PATH)
    print("CNN model loaded successfully.")
except Exception as e:
    model = None
    print(f"ERROR loading model: {e}")


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Malware Detection API is running",
        "model_loaded": model is not None
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }


# ---------------------------------------------------------
# Prediction endpoint
# ---------------------------------------------------------

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    pixels: str = Form(...)
):
    if model is None:
        raise HTTPException(
            status_code=500,
            detail="CNN model could not be loaded."
        )

    # -----------------------------------------------------
    # Validate file type
    # -----------------------------------------------------

    filename = file.filename or "unknown"

    if not filename.lower().endswith(".exe"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a .exe PE file."
        )

    # -----------------------------------------------------
    # Read uploaded file
    # -----------------------------------------------------

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    file_size = len(file_bytes)

    # -----------------------------------------------------
    # Calculate hashes
    # -----------------------------------------------------

    md5_hash = hashlib.md5(file_bytes).hexdigest()

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    # -----------------------------------------------------
    # Receive 1024 grayscale pixel values
    #
    # Frontend architecture:
    #
    # PE bytes
    #     ↓
    # 32 × 32 grayscale
    #     ↓
    # 1024 values
    #     ↓
    # Backend
    #
    # -----------------------------------------------------

    try:
        pixel_values = json.loads(pixels)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid pixel data."
        )

    if not isinstance(pixel_values, list):
        raise HTTPException(
            status_code=400,
            detail="Pixel data must be a list."
        )

    if len(pixel_values) != 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Expected 1024 pixel values, received {len(pixel_values)}."
        )

    # -----------------------------------------------------
    # Convert to NumPy array
    # -----------------------------------------------------

    try:
        image_array = np.array(pixel_values, dtype=np.float32)

        # Training notebook:
        # X_scaled = X.values / 255

        image_array = image_array / 255.0

        # Model input:
        # (1, 32, 32, 1)

        image_array = image_array.reshape(1, 32, 32, 1)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid pixel data: {str(e)}"
        )

    # -----------------------------------------------------
    # CNN prediction
    # -----------------------------------------------------

    prediction_probability = float(
        model.predict(image_array, verbose=0)[0][0]
    )

    # Notebook rule:
    #
    # probability >= 0.5 → Malware
    # probability < 0.5  → Benign

    predicted_label = (
        "Malware"
        if prediction_probability >= 0.5
        else "Benign"
    )

    confidence = (
        prediction_probability
        if prediction_probability >= 0.5
        else 1.0 - prediction_probability
    )

    # -----------------------------------------------------
    # Return result
    # -----------------------------------------------------

    return {
        "filename": filename,
        "file_size": file_size,
        "md5": md5_hash,
        "sha256": sha256_hash,
        "prediction": predicted_label,
        "probability": round(prediction_probability, 6),
        "confidence": round(confidence, 6),
        "label": 1 if prediction_probability >= 0.5 else 0
    }
