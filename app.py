from flask import Flask, request, jsonify, send_file
import os

app = Flask(__name__)

@app.route("/")
def serve_index():
    return send_file('index.html')

@app.route("/style.css")
def serve_css():
    return send_file('style.css')

@app.route("/functions.js")
def serve_js():
    return send_file('functions.js')

@app.route("/api/run", methods=["POST"])
def run_python_code():
    data = request.get_json(force=True) or {}
    product = data.get("product", "")
    country = data.get("country", "")
    result = f"Received product '{product}' for '{country}'"
    return jsonify({"result": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)