


import time
import requests
import json
import yagmail
import os
from dotenv import load_dotenv

load_dotenv()

# Firebase config
FIREBASE_URL = os.getenv("https://iotpro-685a2-default-rtdb.firebaseio.com")  # ending with '/'
FIREBASE_SECRET = os.getenv("AIzaSyC5Ip92e9BAc06CXyDm5Zq_x9szZmu4NKM")


EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

EMAIL_TO = EMAIL_USER  # you can alert yourself

yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)

# Thresholds for anomaly detection
RPM_MAX = 20000
CURRENT_MAX = 5.0  # adjust based on motor
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
    if data['rpm'] > RPM_MAX:
        alerts.append("RPM spike")
    if data['current'] > CURRENT_MAX:
        alerts.append("Current spike")
    if data['temp'] > TEMP_MAX:
        alerts.append("Temperature high")
    return alerts

def send_alert(alerts, data):
    content = f"Motor Alert!\n\nAlerts: {', '.join(alerts)}\nData: {data}"
    try:
        yag.send(EMAIL_TO, "Motor Anomaly Alert", content)
        print("✅ Email alert sent")
    except Exception as e:
        print("Email send failed:", e)

def main_loop():
    while True:
        raw_data = get_raw_data()
        if raw_data:
            alerts = anomaly_detection(raw_data)
            suggestions = {
                "pwm": raw_data['pwm'], 
                "motor": "on" if raw_data['rpm'] > 0 else "off", 
                "alert": ", ".join(alerts) if alerts else ""
            }
            push_suggestions(suggestions)
            if alerts:
                send_alert(alerts, raw_data)
        time.sleep(5)  # run every 5 seconds

if __name__ == "__main__":
    print("ML/Cloud processor started...")
    main_loop()


