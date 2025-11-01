"""
Compliance routes for product analysis
"""

from flask import Blueprint, jsonify, request
import logging
import random

logger = logging.getLogger(__name__)

compliance_bp = Blueprint('compliance', __name__)

# Dependencies will be injected by app.py
redis_client = None
validate_product_input = None
analyze_product_compliance = None
FieldRenderer = None
MarkdownField = None
FormField = None
TextAreaField = None
ButtonField = None


def init_dependencies(redis_instance, validator, analyzer, field_renderer_class,
                      markdown_field, form_field, textarea_field, button_field):
    """Initialize dependencies for this blueprint"""
    global redis_client, validate_product_input, analyze_product_compliance
    global FieldRenderer, MarkdownField, FormField, TextAreaField, ButtonField

    redis_client = redis_instance
    validate_product_input = validator
    analyze_product_compliance = analyzer
    FieldRenderer = field_renderer_class
    MarkdownField = markdown_field
    FormField = form_field
    TextAreaField = textarea_field
    ButtonField = button_field


@compliance_bp.route("/api/run", methods=["POST"])
def run_python_code():
    """Handle product compliance analysis requests"""
    data = request.get_json(force=True) or {}
    product = data.get("product", "")
    country = data.get("country", "")

    # Get field renderer and clear any existing fields
    from routes import fields as fields_module
    if not hasattr(fields_module, 'field_renderer') or fields_module.field_renderer is None:
        fields_module.field_renderer = FieldRenderer()
    else:
        fields_module.field_renderer.clear_blocks()

    # First validate if it's a real product
    is_valid = validate_product_input(product)

    # Increment product search counter (only for valid products)
    if is_valid and product:
        try:
            redis_client.incr('products_searched')
            # Increment norms scouted by random 10-20 for each product
            norms_increment = random.randint(10, 20)
            redis_client.incrby('norms_scouted', norms_increment)
        except Exception as e:
            logger.error(f"Error updating counters: {e}")

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
