from flask import Flask, request, jsonify, send_file
import os
import logging
from dotenv import load_dotenv
from api.fields import field_bp, field_renderer
from api.openrouter import analyze_product_compliance, validate_product_input
from api.field_framework import (FieldRenderer, MarkdownField, FormField,
                                  TextAreaField, ButtonField)

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

@app.route("/bp")
def serve_business_plan():
    """Serve the interactive business plan / investment model"""
    return send_file('static/bp.html')

@app.route("/api/run", methods=["POST"])
def run_python_code():
    """Handle product compliance analysis requests"""
    data = request.get_json(force=True) or {}
    product = data.get("product", "")
    country = data.get("country", "")

    # Get field renderer and clear any existing fields
    import api.fields as fields_module
    if not hasattr(fields_module, 'field_renderer') or fields_module.field_renderer is None:
        fields_module.field_renderer = FieldRenderer()
    else:
        fields_module.field_renderer.clear_blocks()

    # First validate if it's a real product
    is_valid = validate_product_input(product)

    if not is_valid:
        # Create error block
        block = fields_module.field_renderer.create_block("error_block", "")
        block.add_field(MarkdownField("error", "### No product detected"))
        block.add_field(MarkdownField("hint", "Please enter a real product description (e.g., 'wireless headphones', 'coffee maker', 'laptop computer') and try again."))
        block.add_field(MarkdownField("tip", "*Tip: Describe what the product is and what it does.*"))

        # Add feedback button
        feedback_btn_block = fields_module.field_renderer.create_block("feedback_button", "")
        feedback_btn_block.add_field(ButtonField("mistake_btn", "You think we made a mistake?", action="expand"))

        # Add hidden feedback form
        form_block = fields_module.field_renderer.create_block("feedback_form", "", hidden=True)
        form_block.add_field(MarkdownField("form_title", "### Help us improve"))
        form_block.add_field(MarkdownField("form_desc", "If this is a real product, please let us know:"))
        form_block.add_field(FormField("name", "Your Name", "John Doe", input_type="text"))
        form_block.add_field(FormField("email", "Your Email", "john@example.com", input_type="email", required=True))
        form_block.add_field(FormField("product", "", "", input_type="hidden", value=product))
        form_block.add_field(TextAreaField("message", "Why is this a real product?", "Please explain what this product is and what it does..."))
        form_block.submit_endpoint = "/api/feedback/submit"
        form_block.set_button_text("Send Feedback")

        return jsonify({
            "result": "Invalid product description",
            "product": product,
            "country": country,
            "status": "invalid",
            "show_fields": True  # Signal frontend to load fields
        })

    # Valid product - clear fields and proceed with normal analysis
    fields_module.field_renderer.clear_blocks()
    result = analyze_product_compliance(product, country)

    # Return appropriate HTTP status based on result
    if result.get("status") == "error":
        return jsonify(result), 500
    return jsonify(result)

# Core API is ready

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)