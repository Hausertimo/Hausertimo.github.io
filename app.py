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
from flask import Flask
import logging
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')

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

# Import blueprints
from routes.main import main_bp
from routes.analytics import analytics_bp, init_redis as init_analytics_redis
from routes.compliance import compliance_bp, init_dependencies as init_compliance_deps
from routes.fields import field_bp
from routes.develope import develope_bp

# Import services
from services.openrouter import analyze_product_compliance, validate_product_input
from services.field_framework import (FieldRenderer, MarkdownField, FormField,
                                      TextAreaField, ButtonField)

# Register all blueprints
app.register_blueprint(main_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(compliance_bp)
app.register_blueprint(field_bp)
app.register_blueprint(develope_bp)

# Initialize blueprint dependencies
init_analytics_redis(redis_client)
init_compliance_deps(
    redis_client,
    validate_product_input,
    analyze_product_compliance,
    FieldRenderer,
    MarkdownField,
    FormField,
    TextAreaField,
    ButtonField
)

logger.info("All blueprints registered successfully")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
