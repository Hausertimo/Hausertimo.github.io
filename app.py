from flask import Flask, request, jsonify, send_file
import os
import logging
from dotenv import load_dotenv
from api.fields import field_bp, field_renderer
from api.openrouter import analyze_product_compliance, validate_product_input
from api.field_framework import FieldRenderer, MarkdownField

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

    # First validate if it's a real product
    is_valid = validate_product_input(product)

    if not is_valid:
        # Create field renderer with error message
        from api.fields import field_renderer
        import api.fields as fields_module

        fields_module.field_renderer = FieldRenderer()

        block = fields_module.field_renderer.create_block("error_block", "")
        block.add_field(MarkdownField("error", "### No product detected"))
        block.add_field(MarkdownField("hint", "Please enter a real product description (e.g., 'wireless headphones', 'coffee maker', 'laptop computer') and try again."))
        block.add_field(MarkdownField("tip", "*Tip: Describe what the product is and what it does.*"))

        return jsonify({
            "result": "Invalid product description",
            "product": product,
            "country": country,
            "status": "invalid",
            "show_fields": True  # Signal frontend to load fields
        })

    # Valid product - proceed with normal analysis
    result = analyze_product_compliance(product, country)

    # Return appropriate HTTP status based on result
    if result.get("status") == "error":
        return jsonify(result), 500
    return jsonify(result)

# Core API is ready

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)