from flask import Flask, request, jsonify, send_file
import os
import logging
from dotenv import load_dotenv
from api.fields import field_bp
from api.openrouter import analyze_product_compliance

# Load environment variables from .env file
# Look for .env in parent directory (Website folder)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")
else:
    # Try current directory
    load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')

# Register the field API blueprint
app.register_blueprint(field_bp)

@app.route("/")
def serve_index():
    return send_file('static/index.html')

@app.route("/api/run", methods=["POST"])
def run_python_code():
    """Handle product compliance analysis requests"""
    data = request.get_json(force=True) or {}
    product = data.get("product", "")
    country = data.get("country", "")

    # Call the extracted OpenRouter API function
    result = analyze_product_compliance(product, country)

    # Return appropriate HTTP status based on result
    if result.get("status") == "error":
        return jsonify(result), 500
    return jsonify(result)

# Core API is ready

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)