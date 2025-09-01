from flask import Flask, request, jsonify

app = Flask(__name__)

# API route to simulate prediction
@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    rpm = data.get("rpm", 0)
    temp = data.get("temp", None)

    # Very dummy logic for motor status
    if rpm < 100:
        status = "Faulty"
        suggestion = "Motor not running or sensor not connected."
    elif rpm < 800:
        status = "Underload"
        suggestion = "Motor running below expected speed."
    else:
        status = "Healthy"
        suggestion = "Motor running normally."

    # Check temperature condition
    if temp is not None and temp > 50:
        status = "Overheating"
        suggestion = "Check cooling or reduce load."

    return jsonify({
        "status": status,
        "suggestion": suggestion,
        "rpm": rpm,
        "temp": temp
    })

@app.route("/", methods=["GET"])
def home():
    return "Motor ML API is running with RPM + Temp support!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

