"""
Analytics routes for tracking metrics
"""

from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__)

# Redis client will be set by app.py
redis_client = None


def init_redis(redis_instance):
    """Initialize redis client for this blueprint"""
    global redis_client
    redis_client = redis_instance


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
