import os
import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, db

# ---------------- ENV VARIABLES ----------------
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
FIREBASE_URL = os.getenv("FIREBASE_URL")
FIREBASE_SECRET = os.getenv("FIREBASE_SECRET")  # optional if using serviceAccount

# ---------------- THRESHOLDS ----------------
RPM_MAX = 5000
CURRENT_MAX = 5.0  # Amps
VOLTAGE_MIN = 10.0
VOLTAGE_MAX = 15.0

# ---------------- FLASK APP ----------------
app = Flask(__name__)

# ---------------- FIREBASE INIT ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": "iotpro-685a2",
        "private_key_id": "dummy",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEv...\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk@iotpro-685a2.iam.gserviceaccount.com",
        "client_id": "dummy",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk"
    })
    firebase_admin.initialize_app(cred, {
        "databaseURL": FIREBASE_URL
    })

# ---------------- EMAIL ALERT ----------------
def send_email_alert(subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())
        server.quit()
        print("✅ Email sent:", subject)
    except Exception as e:
        print("❌ Email failed:", e)

# ---------------- ANOMALY DETECTION ----------------
def anomaly_detection(data):
    alerts = []

    # Safe get to avoid KeyError
    rpm = data.get("rpm")
    current = data.get("current")
    voltage = data.get("voltage")

    if rpm is not None and rpm > RPM_MAX:
        alerts.append(f"⚠️ RPM too high: {rpm}")

    if current is not None and current > CURRENT_MAX:
        alerts.append(f"⚠️ Current too high: {current}")

    if voltage is not None and (voltage < VOLTAGE_MIN or voltage > VOLTAGE_MAX):
        alerts.append(f"⚠️ Voltage anomaly: {voltage}")

    return alerts

# ---------------- BACKGROUND LOOP ----------------
def main_loop():
    ref = db.reference("motor_data")
    while True:
        try:
            raw_data = ref.get() or {}
            print("Incoming data:", raw_data)

            alerts = anomaly_detection(raw_data)
            for alert in alerts:
                send_email_alert("Motor Alert", alert)

        except Exception as e:
            print("❌ Error in loop:", e)

        time.sleep(5)

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return jsonify({"status": "running", "service": "motor-ml"})

# ---------------- START ----------------
if __name__ == "__main__":
    # Run background loop
    t = threading.Thread(target=main_loop, daemon=True)
    t.start()
    
    # Start Flask server
    app.run(host="0.0.0.0", port=10000)
