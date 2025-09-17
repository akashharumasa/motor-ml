# main.py (Isolation Forest anomaly detection API with dual Firebase write)
from fastapi import FastAPI, HTTPException
from datetime import datetime
import numpy as np
import joblib
import os
import firebase_admin
from firebase_admin import credentials, db

# --- Firebase config ---
SERVICE_ACCOUNT_FILE = "serviceAccountKey.json"
DATABASE_URL = "https://iotpro-685a2-default-rtdb.firebaseio.com"

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
    firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

app = FastAPI()

# --- Load per-PWM models safely ---
models = {}
for pwm in [64, 128, 192, 255]:
    model_path = f"models/model_pwm{pwm}.pkl"
    if os.path.exists(model_path):
        loaded = joblib.load(model_path)
        # Each file contains (scaler, model)
        if isinstance(loaded, tuple) and len(loaded) == 2:
            models[pwm] = {"scaler": loaded[0], "model": loaded[1]}
        else:
            models[pwm] = {"scaler": None, "model": loaded}
        print(f"✅ Loaded model for PWM {pwm}")
    else:
        print(f"⚠️ Model file not found: {model_path}")

# Features now only Voltage + Current_mA
features = ["Voltage", "Current_mA"]

# --- Classify a sample ---
def classify_sample(sample):
    pwm = int(sample.get("PWM", 0))
    entry = models.get(pwm)
    if not entry or not entry.get("model"):
        return f"Error: No model for PWM {pwm}"

    # Extract just the two features
    X = np.array([[float(sample.get(f, 0)) for f in features]])

    scaler = entry.get("scaler")
    if scaler:
        X = scaler.transform(X)

    model = entry["model"]
    pred = model.predict(X)  # +1 = normal, -1 = anomaly
    return "Normal" if pred[0] == 1 else "Bad"

# --- PWM Normalizer ---
def normalize_pwm(pwm):
    if pwm == 191:   # 75% button sends 191
        return 192
    return pwm

# --- Routes ---
@app.get("/")
def home():
    return {"message": "Isolation Forest Anomaly Detection API running"}

@app.post("/predict")
def predict(payload: dict):
    pwm = int(payload.get("PWM", -1))
    pwm = normalize_pwm(pwm)  # 191 → 192

    # Update payload PWM so classifier sees normalized value
    payload["PWM"] = pwm

    if pwm == 0:
        status = "Motor Off"
    elif pwm in [64, 128, 192, 255]:
        try:
            status = classify_sample(payload)  # now sees 192
        except Exception as e:
            status = f"Prediction failed: {e}"
    else:
        status = "Unknown PWM"

    # --- Write results to Firebase ---
    try:
        root_ref = db.reference("/")
        data = {
            "PWM": pwm,
            "Status": status,
            "Voltage": payload.get("Voltage"),
            "Current_mA": payload.get("Current_mA"),
            "Power_mW": payload.get("Power_mW"),
            "Temp_C": payload.get("Temp_C"),
            "Vib_per_s": payload.get("Vib_per_s"),
            "CheckedAt": datetime.utcnow().isoformat() + "Z"
        }

        # Keep full history
        root_ref.child("SensorDataHistory").push(data)

        # Always overwrite latest
        root_ref.child("SensorDataLatest").set(data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firebase write failed: {e}")

    return {"status": status, "written_to": ["/SensorDataLatest", "/SensorDataHistory"]}

