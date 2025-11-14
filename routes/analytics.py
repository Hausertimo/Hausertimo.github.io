"""
Analytics routes for tracking metrics
"""

from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)

# Redis client will be set by app.py
redis_client = None
# Supabase client will be set by app.py
supabase_client = None


def init_redis(redis_instance):
    """Initialize redis client for this blueprint"""
    global redis_client
    redis_client = redis_instance


def init_supabase(supabase_instance):
    """Initialize supabase client for this blueprint"""
    global supabase_client
    supabase_client = supabase_instance


def get_total_signups():
    """Get total number of registered users from Supabase"""
    try:
        if not supabase_client:
            logger.warning("Supabase client not initialized")
            return 0

        # Query Supabase auth users table to get count
        response = supabase_client.auth.admin.list_users()

        if response:
            # Count total users
            total_users = len(response) if isinstance(response, list) else 0
            return total_users
        return 0
    except Exception as e:
        logger.error(f"Error getting Supabase user count: {e}")
        return 0


@analytics_bp.route("/api/visitor-count", methods=["GET", "POST"])
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


@analytics_bp.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Get all metrics for display"""
    try:
        # Get products searched count (start at 50)
        products_count = redis_client.get('products_searched')
        if products_count is None:
            redis_client.set('products_searched', 50)
            products_count = 50

        # Fixed value for norms cataloged
        norms_cataloged = 400

        # Get total signups from Supabase
        total_signups = get_total_signups()

        return jsonify({
            "products_searched": int(products_count),
            "norms_cataloged": norms_cataloged,
            "total_signups": total_signups
        })

    except Exception as e:
        logger.error(f"Error in metrics: {e}")
        return jsonify({"error": "Metrics temporarily unavailable"}), 503
