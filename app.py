import os
from dotenv import load_dotenv

# Load environment variables FIRST, before importing modules that need them
# Look for .env in parent directory (Website folder)
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")
else:
    # Try current directory
    load_dotenv()
    print("Loaded .env from current directory")

# Now import everything else after env vars are loaded
from flask import Flask, request, jsonify, send_file
import logging
import redis
import json
from api.fields import field_bp, field_renderer
from api.openrouter import analyze_product_compliance, validate_product_input
from api.field_framework import (FieldRenderer, MarkdownField, FormField,
                                  TextAreaField, ButtonField)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')

# Register the field API blueprint
app.register_blueprint(field_bp)

# Initialize Redis connection (REQUIRED)
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    logger.error("REDIS_URL not configured! Set it in Fly.io Secrets")
    raise RuntimeError("Redis is required. No REDIS_URL found in environment.")

try:
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connected successfully")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")
    raise RuntimeError(f"Could not connect to Redis: {e}")

@app.route("/")
def serve_index():
    return send_file('static/index.html')

@app.route("/bp")
def serve_business_plan():
    """Serve the interactive business plan / investment model"""
    return send_file('static/bp.html')

@app.route("/api/visitor-count", methods=["GET", "POST"])
def visitor_count():
    """Get and increment visitor count - counts every page view"""
    try:
        if request.method == "POST":
            # Increment counter on every POST (every page load)
            count = redis_client.incr('monthly_users')
        else:
            # Just get current count on GET
            count = redis_client.get('monthly_users')
            if count is None:
                # Initialize if not exists
                redis_client.set('monthly_users', 413)
                count = 413

        return jsonify({"count": int(count)})

    except Exception as e:
        logger.error(f"Redis error in visitor count: {e}")
        return jsonify({"error": "Counter temporarily unavailable"}), 503

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Get all metrics for display"""
    try:
        # Get products searched count (start at 703)
        products_count = redis_client.get('products_searched')
        if products_count is None:
            redis_client.set('products_searched', 703)
            products_count = 703

        # Get norms scouted count (start at 6397)
        norms_count = redis_client.get('norms_scouted')
        if norms_count is None:
            redis_client.set('norms_scouted', 6397)
            norms_count = 6397

        # Get monthly users
        users_count = redis_client.get('monthly_users') or 413

        return jsonify({
            "products_searched": int(products_count),
            "norms_scouted": int(norms_count),
            "monthly_users": int(users_count)
        })

    except Exception as e:
        logger.error(f"Redis error in metrics: {e}")
        return jsonify({"error": "Metrics temporarily unavailable"}), 503

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

    # Increment product search counter (only for valid products)
    if is_valid and product:
        try:
            redis_client.incr('products_searched')
            # Increment norms scouted by random 10-20 for each product
            import random
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

# Core API is ready

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)