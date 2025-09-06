import os
import json
import threading
import time
from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, db

# -----------------------------
# Firebase Setup (from env var)
# -----------------------------
firebase_key_json = os.getenv("FIREBASE_KEY")

if not firebase_key_json:
    raise ValueError("❌ FIREBASE_KEY environment variable not set in Render!")

# If Render stored it with \n instead of real newlines, fix it
firebase_key_json = firebase_key_json.replace('\\n', '\n')

firebase_key_dict = json.loads(firebase_key_json)

cred = credentials.Certificate(firebase_key_dict)

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://your-project-id.firebaseio.com/"  # 👈 replace with your DB URL
})

# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__)

# Example thresholds
RPM_MAX = 5000
TEMP_MAX = 80
CURR_MAX = 10

def anomaly_detection(data):
    """Check if motor values exceed limits"""
    alerts = []
    if "rpm" in data and data["rpm"] > RPM_MAX:
        alerts.append("High RPM detected")
    if "temperature" in data and data["temperature"] > TEMP_MAX:
        alerts.append("Overheating detected")
    if "current" in data and data["current"] > CURR_MAX:
        alerts.append("Overcurrent detected")
    return alerts

def fetch_motor_data():
    """Fetch motor data from Firebase"""
    ref = db.reference("/motor_data")
    data = ref.get()
    return data or {}

def main_loop():
    """Background loop to monitor data"""
    while True:
        raw_data = fetch_motor_data()
        alerts = anomaly_detection(raw_data)

        if alerts:
            print("⚠️ Alerts:", alerts)
        else:
            print("✅ Motor running normally")

        time.sleep(5)  # check every 5 seconds

# -----------------------------
# API Routes
# -----------------------------
@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "Motor monitoring system running"})

@app.route("/data")
def get_data():
    data = fetch_motor_data()
    alerts = anomaly_detection(data)
    return jsonify({"data": data, "alerts": alerts})

# -----------------------------
# Start background thread + app
# -----------------------------
if __name__ == "__main__":
    t = threading.Thread(target=main_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000)

