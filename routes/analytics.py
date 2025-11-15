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

        # Query workspaces to count distinct users (users who have created workspaces)
        response = supabase_client.table('workspaces').select('user_id', count='exact').execute()

        if response and hasattr(response, 'count'):
            # Get count of distinct user_ids
            result = supabase_client.rpc('count_distinct_users').execute()
            if result and result.data is not None:
                return result.data
            # Fallback: just return workspace count as proxy
            return response.count if response.count else 0
        return 0
    except Exception as e:
        logger.error(f"Error getting Supabase user count: {e}")
        # Fallback: try to count workspaces
        try:
            response = supabase_client.table('workspaces').select('id', count='exact').execute()
            # Return approximate count based on workspaces (rough estimate)
            workspace_count = response.count if response and hasattr(response, 'count') else 0
            # Assume average 2 workspaces per user as rough estimate
            return max(1, workspace_count // 2) if workspace_count > 0 else 0
        except:
            return 0


def get_active_products():
    """Get total number of workspaces (active products) from Supabase"""
    try:
        if not supabase_client:
            logger.warning("Supabase client not initialized")
            return 0

        # Query workspaces table to get count
        response = supabase_client.table('workspaces').select('id', count='exact').execute()

        if response and hasattr(response, 'count'):
            return response.count if response.count else 0
        return 0
    except Exception as e:
        logger.error(f"Error getting workspace count: {e}")
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
        # Get active products count from Supabase workspaces table
        active_products = get_active_products()

        # Fixed value for norms cataloged
        norms_cataloged = 400

        # Get total signups from Supabase
        total_signups = get_total_signups()

        return jsonify({
            "active_products": active_products,
            "norms_cataloged": norms_cataloged,
            "total_signups": total_signups
        })

    except Exception as e:
        logger.error(f"Error in metrics: {e}")
        return jsonify({"error": "Metrics temporarily unavailable"}), 503
