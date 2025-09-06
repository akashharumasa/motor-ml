from flask import Flask, jsonify
import requests
import yagmail
import os
import threading
import time

# Flask app
app = Flask(__name__)

# Firebase config (use Render env variables!)
FIREBASE_URL = os.getenv("FIREBASE_URL")  # e.g. https://your-db.firebaseio.com
FIREBASE_SECRET = os.getenv("FIREBASE_SECRET")

# Email config
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = EMAIL_USER

yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)

# Thresholds
RPM_MAX = 20000
CURRENT_MAX = 5.0
TEMP_MAX = 70


def get_raw_data():
    try:
        r = requests.get(f"{FIREBASE_URL}/motor/raw.json?auth={FIREBASE_SECRET}")
        if r.status_code == 200:
            return r.json()
        else:
            print("Firebase read error", r.status_code)
            return None
    except Exception as e:
        print("Firebase read exception:", e)
        return None


def push_suggestions(suggestions):
    try:
        requests.patch(f"{FIREBASE_URL}/motor/ml_suggestions.json?auth={FIREBASE_SECRET}",
                       json=suggestions)
    except Exception as e:
        print("Firebase push exception:", e)


def anomaly_detection(data):
    alerts = []
    if data.get('rpm', 0) > RPM_MAX:
        alerts.append("RPM spike")
    if data.get('current', 0) > CURRENT_MAX:
        alerts.append("Current spike")
    if data.get('temp', 0) > TEMP_MAX:
        alerts.append("Temperature high")
    return alerts


def send_alert(alerts, data):
    content = f"Motor Alert!\n\nAlerts: {', '.join(alerts)}\nData: {data}"
    try:
        yag.send(EMAIL_TO, "Motor Anomaly Alert", content)
        print("✅ Email alert sent")
    except Exception as e:
        print("Email send failed:", e)


def worker_loop():
    while True:
        raw_data = get_raw_data()
        if raw_data:
            alerts = anomaly_detection(raw_data)
            suggestions = {
                "pwm": raw_data.get('pwm', 0),
                "motor": "on" if raw_data.get('rpm', 0) > 0 else "off",
                "alert": ", ".join(alerts) if alerts else ""
            }
            push_suggestions(suggestions)
            if alerts:
                send_alert(alerts, raw_data)
        time.sleep(5)


# Start background thread after app loads
@app.before_first_request
def start_worker():
    thread = threading.Thread(target=worker_loop, daemon=True)
    thread.start()


# Test route
@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "🚀 IoT Cloud Service Running"})


@app.route("/ping")
def ping():
    return "pong"

