"""
Tracking Routes Blueprint

Handles all tracking-related API endpoints.
Designed to be portable and easy to integrate into any Flask application.

Endpoints:
- POST /api/tracking/event - Store tracking events
- GET /api/tracking/analytics - Get analytics summary
- GET /api/tracking/session/<session_id> - Get session data
- DELETE /api/tracking/session/<session_id> - Delete session data (GDPR)
- GET /api/tracking/journey/<session_id> - Get user journey
- GET /api/tracking/page-metrics - Get page-level metrics
- GET /analytics - Analytics dashboard page
"""

from flask import Blueprint, request, jsonify, render_template, send_from_directory
from datetime import datetime, timedelta
import logging
import os

# Create blueprint
tracking_bp = Blueprint('tracking', __name__)

# Logging
logger = logging.getLogger(__name__)


def init_tracking_routes(app, redis_client):
    """
    Initialize tracking routes with dependencies.

    Args:
        app: Flask application instance
        redis_client: Redis client for storage

    Returns:
        Configured blueprint
    """
    from services.tracking_storage import TrackingStorage

    # Create storage instance
    storage = TrackingStorage(redis_client, key_prefix="normscout_tracking")

    # Store in app config for access in routes
    app.config['TRACKING_STORAGE'] = storage

    # Register blueprint
    app.register_blueprint(tracking_bp)

    logger.info("Tracking routes initialized")
    return tracking_bp


# ============================================================================
# EVENT TRACKING ENDPOINTS
# ============================================================================

@tracking_bp.route('/api/tracking/event', methods=['POST'])
def track_event():
    """
    Store tracking events.

    Expected payload:
    {
        "events": [
            {
                "session_id": "uuid",
                "timestamp": "ISO-8601",
                "event_type": "page_view|click|scroll_depth|etc",
                "page": "/path",
                ...additional event data
            }
        ]
    }

    Returns:
        JSON response with status
    """
    try:
        from flask import current_app
        storage = current_app.config.get('TRACKING_STORAGE')

        if not storage:
            logger.error("Tracking storage not initialized")
            return jsonify({"error": "Tracking not configured"}), 500

        # Get events from request
        data = request.get_json()
        if not data or "events" not in data:
            return jsonify({"error": "Invalid payload"}), 400

        events = data.get("events", [])
        if not events:
            return jsonify({"status": "no_events"}), 200

        # Validate events
        valid_events = []
        for event in events:
            if not event.get("session_id"):
                logger.warning("Event missing session_id, skipping")
                continue

            # Ensure timestamp exists
            if not event.get("timestamp"):
                event["timestamp"] = datetime.utcnow().isoformat()

            valid_events.append(event)

        if not valid_events:
            return jsonify({"error": "No valid events"}), 400

        # Store events
        stored_count = storage.store_events(valid_events)

        # Update session metadata for first event
        if valid_events:
            first_event = valid_events[0]
            session_id = first_event.get("session_id")

            session_data = {
                "user_agent": first_event.get("user_agent", ""),
                "language": first_event.get("language", ""),
                "viewport": f"{first_event.get('viewport_width', 0)}x{first_event.get('viewport_height', 0)}",
                "event_count": len(valid_events)
            }

            storage.create_or_update_session(session_id, session_data)
            storage.increment_session_counter(session_id, "total_events", len(valid_events))

        logger.info(f"Stored {stored_count} tracking events")

        return jsonify({
            "status": "success",
            "stored": stored_count
        }), 200

    except Exception as e:
        logger.error(f"Error storing tracking events: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@tracking_bp.route('/api/tracking/analytics', methods=['GET'])
def get_analytics():
    """
    Get analytics summary.

    Query parameters:
        days (optional): Number of days to look back (default: 7)

    Returns:
        JSON with analytics data
    """
    try:
        from flask import current_app
        storage = current_app.config.get('TRACKING_STORAGE')

        if not storage:
            return jsonify({"error": "Tracking not configured"}), 500

        # Get days parameter
        days = request.args.get('days', default=7, type=int)
        days = max(1, min(days, 90))  # Limit between 1 and 90 days

        # Get summary
        summary = storage.get_analytics_summary(days=days)

        return jsonify(summary), 200

    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@tracking_bp.route('/api/tracking/page-metrics', methods=['GET'])
def get_page_metrics():
    """
    Get metrics for all pages or a specific page.

    Query parameters:
        page (optional): Specific page path

    Returns:
        JSON with page metrics
    """
    try:
        from flask import current_app
        storage = current_app.config.get('TRACKING_STORAGE')

        if not storage:
            return jsonify({"error": "Tracking not configured"}), 500

        page = request.args.get('page')

        if page:
            # Get specific page metrics
            metrics = storage.get_page_metrics(page)
            return jsonify(metrics), 200
        else:
            # Get all page metrics
            metrics = storage.get_all_page_metrics()
            return jsonify({"pages": metrics}), 200

    except Exception as e:
        logger.error(f"Error getting page metrics: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@tracking_bp.route('/api/tracking/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """
    Get session data.

    Args:
        session_id: Session identifier

    Returns:
        JSON with session data
    """
    try:
        from flask import current_app
        storage = current_app.config.get('TRACKING_STORAGE')

        if not storage:
            return jsonify({"error": "Tracking not configured"}), 500

        session = storage.get_session(session_id)

        if not session:
            return jsonify({"error": "Session not found"}), 404

        return jsonify(session), 200

    except Exception as e:
        logger.error(f"Error getting session: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@tracking_bp.route('/api/tracking/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    Delete session data (GDPR right to deletion).

    Args:
        session_id: Session identifier

    Returns:
        JSON with status
    """
    try:
        from flask import current_app
        storage = current_app.config.get('TRACKING_STORAGE')

        if not storage:
            return jsonify({"error": "Tracking not configured"}), 500

        success = storage.delete_session_data(session_id)

        if success:
            logger.info(f"Deleted session data for {session_id}")
            return jsonify({"status": "deleted"}), 200
        else:
            return jsonify({"error": "Failed to delete"}), 500

    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@tracking_bp.route('/api/tracking/journey/<session_id>', methods=['GET'])
def get_user_journey(session_id):
    """
    Get complete user journey for a session.

    Args:
        session_id: Session identifier

    Returns:
        JSON with journey data
    """
    try:
        from flask import current_app
        storage = current_app.config.get('TRACKING_STORAGE')

        if not storage:
            return jsonify({"error": "Tracking not configured"}), 500

        journey = storage.get_user_journey(session_id)

        return jsonify(journey), 200

    except Exception as e:
        logger.error(f"Error getting user journey: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@tracking_bp.route('/api/tracking/export/<session_id>', methods=['GET'])
def export_session(session_id):
    """
    Export session data (GDPR data portability).

    Args:
        session_id: Session identifier

    Returns:
        JSON with complete session data
    """
    try:
        from flask import current_app
        storage = current_app.config.get('TRACKING_STORAGE')

        if not storage:
            return jsonify({"error": "Tracking not configured"}), 500

        data = storage.export_session_data(session_id)

        return jsonify(data), 200

    except Exception as e:
        logger.error(f"Error exporting session: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# ANALYTICS DASHBOARD
# ============================================================================

@tracking_bp.route('/analytics', methods=['GET'])
def analytics_dashboard():
    """
    Render analytics dashboard page.

    Returns:
        HTML analytics dashboard
    """
    try:
        # Check if analytics.html template exists
        template_path = os.path.join('templates', 'analytics.html')
        if os.path.exists(template_path):
            return render_template('analytics.html')
        else:
            # Return static HTML if template doesn't exist
            return send_from_directory('static', 'analytics.html')

    except Exception as e:
        logger.error(f"Error rendering analytics dashboard: {str(e)}", exc_info=True)
        return "Analytics dashboard temporarily unavailable", 500


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@tracking_bp.route('/api/tracking/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON with health status
    """
    try:
        from flask import current_app
        storage = current_app.config.get('TRACKING_STORAGE')

        if not storage:
            return jsonify({"status": "unhealthy", "reason": "Storage not initialized"}), 500

        # Try to ping Redis
        storage.redis.ping()

        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "reason": str(e)
        }), 500
