from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def health():
    return "Flask backend is live!"

@app.route("/api/run", methods=["POST"])
def run_python_code():
    data = request.get_json(force=True) or {}
    product = data.get("product", "")
    country = data.get("country", "")
    result = f"Received product '{product}' for '{country}'"
    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)