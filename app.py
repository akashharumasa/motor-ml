from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Dummy training dataset (replace later with your motor dataset)
training_data = [
    {"voltage": 12, "current": 1.2, "rpm": 1500, "status": "Healthy"},
    {"voltage": 12, "current": 2.5, "rpm": 1200, "status": "Overload"},
    {"voltage": 11, "current": 0.8, "rpm": 900, "status": "Underload"},
    {"voltage": 10, "current": 1.5, "rpm": 700, "status": "Faulty"},
]

# API route to simulate prediction
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    voltage = data.get("voltage")
    current = data.get("current")
    rpm = data.get("rpm")

    # Very dummy logic (ML will replace later)
    if current > 2:
        status = "Overload"
        suggestion = "Reduce load or check motor bearings."
    elif current < 1:
        status = "Underload"
        suggestion = "Increase load or check for disconnection."
    elif rpm < 800:
        status = "Faulty"
        suggestion = "Motor might be damaged or wiring issue."
    else:
        status = "Healthy"
        suggestion = "Motor running normally."

    return jsonify({
        "status": status,
        "suggestion": suggestion
    })

@app.route("/", methods=["GET"])
def home():
    return "Motor ML API is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
