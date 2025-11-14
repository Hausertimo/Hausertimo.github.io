"""
Tracking Storage Service

Handles storage and retrieval of user tracking data in Redis.
Designed to be portable and easy to use across multiple sites.

Data Structure:
- session:{session_id} - Hash containing session metadata
- events:{session_id} - List of event JSONs
- daily_sessions:{date} - Set of unique session IDs
- page_metrics:{page_path} - Hash containing aggregated metrics
- hourly_events:{date}:{hour} - Counter for events per hour
"""

import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class TrackingStorage:
    """
    Portable tracking storage service that works with Redis.

    Can be easily configured for different sites by changing key prefixes.
    """

    def __init__(self, redis_client, key_prefix="tracking"):
        """
        Initialize tracking storage.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for all Redis keys (useful for multi-site deployments)
        """
        self.redis = redis_client
        self.prefix = key_prefix

        # Default retention periods (in seconds)
        self.SESSION_TTL = 30 * 24 * 60 * 60  # 30 days
        self.EVENT_TTL = 30 * 24 * 60 * 60    # 30 days
        self.METRICS_TTL = 90 * 24 * 60 * 60  # 90 days

    def _key(self, *parts):
        """Generate a namespaced Redis key."""
        return f"{self.prefix}:" + ":".join(str(p) for p in parts)

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    def create_or_update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Create or update a session.

        Args:
            session_id: Unique session identifier
            session_data: Dictionary of session metadata

        Returns:
            True if successful
        """
        key = self._key("session", session_id)

        # Add timestamp if not present
        if "first_seen" not in session_data:
            session_data["first_seen"] = datetime.utcnow().isoformat()

        session_data["last_seen"] = datetime.utcnow().isoformat()

        # Store in Redis
        pipeline = self.redis.pipeline()
        pipeline.hset(key, mapping=session_data)
        pipeline.expire(key, self.SESSION_TTL)
        pipeline.execute()

        return True

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        key = self._key("session", session_id)
        data = self.redis.hgetall(key)

        if not data:
            return None

        # Data is already decoded (decode_responses=True)
        return data

    def increment_session_counter(self, session_id: str, field: str, amount: int = 1):
        """Increment a counter in session data."""
        key = self._key("session", session_id)
        self.redis.hincrby(key, field, amount)

    # ========================================================================
    # EVENT STORAGE
    # ========================================================================

    def store_events(self, events: List[Dict[str, Any]]) -> int:
        """
        Store multiple events.

        Args:
            events: List of event dictionaries

        Returns:
            Number of events stored
        """
        if not events:
            return 0

        pipeline = self.redis.pipeline()

        for event in events:
            session_id = event.get("session_id")
            if not session_id:
                continue

            # Store event in session's event list
            event_key = self._key("events", session_id)
            pipeline.rpush(event_key, json.dumps(event))
            pipeline.expire(event_key, self.EVENT_TTL)

            # Update session metadata
            session_key = self._key("session", session_id)
            pipeline.hset(session_key, "last_seen", datetime.utcnow().isoformat())
            pipeline.expire(session_key, self.SESSION_TTL)

            # Add to daily sessions set
            today = datetime.utcnow().strftime("%Y-%m-%d")
            daily_key = self._key("daily_sessions", today)
            pipeline.sadd(daily_key, session_id)
            pipeline.expire(daily_key, self.METRICS_TTL)

            # Increment hourly event counter
            hour = datetime.utcnow().strftime("%Y-%m-%d:%H")
            hourly_key = self._key("hourly_events", hour)
            pipeline.incr(hourly_key)
            pipeline.expire(hourly_key, self.METRICS_TTL)

            # Update page metrics
            if "page" in event:
                self._update_page_metrics_pipeline(pipeline, event)

        pipeline.execute()
        return len(events)

    def get_session_events(self, session_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all events for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of events to return (newest first)

        Returns:
            List of event dictionaries
        """
        key = self._key("events", session_id)

        if limit:
            # Get last N events
            events_raw = self.redis.lrange(key, -limit, -1)
        else:
            # Get all events
            events_raw = self.redis.lrange(key, 0, -1)

        events = []
        for event_json in events_raw:
            try:
                events.append(json.loads(event_json))
            except json.JSONDecodeError:
                continue

        return events

    # ========================================================================
    # PAGE METRICS
    # ========================================================================

    def _update_page_metrics_pipeline(self, pipeline, event: Dict[str, Any]):
        """Update page-level metrics (used within a pipeline)."""
        page = event.get("page")
        if not page:
            return

        metrics_key = self._key("page_metrics", page)

        # Increment view count
        if event.get("event_type") == "page_view":
            pipeline.hincrby(metrics_key, "views", 1)

        # Update time spent (if available)
        time_on_page = event.get("time_on_page")
        if time_on_page:
            pipeline.hincrby(metrics_key, "total_time", int(time_on_page))
            pipeline.hincrby(metrics_key, "time_samples", 1)

        # Track scroll depth
        if event.get("event_type") == "scroll_depth":
            depth = event.get("depth_percent", 0)
            if depth >= 75:
                pipeline.hincrby(metrics_key, "scroll_75", 1)
            if depth >= 90:
                pipeline.hincrby(metrics_key, "scroll_90", 1)

        # Set expiry
        pipeline.expire(metrics_key, self.METRICS_TTL)

    def get_page_metrics(self, page: str) -> Dict[str, Any]:
        """Get aggregated metrics for a specific page."""
        key = self._key("page_metrics", page)
        data = self.redis.hgetall(key)

        if not data:
            return {
                "page": page,
                "views": 0,
                "avg_time": 0,
                "engagement_rate": 0
            }

        # Convert to integers (data is already decoded)
        metrics = {k: int(v) for k, v in data.items()}

        # Calculate averages
        views = metrics.get("views", 0)
        total_time = metrics.get("total_time", 0)
        time_samples = metrics.get("time_samples", 1)
        scroll_75 = metrics.get("scroll_75", 0)

        return {
            "page": page,
            "views": views,
            "avg_time": round(total_time / time_samples, 1) if time_samples > 0 else 0,
            "engagement_rate": round((scroll_75 / views * 100), 1) if views > 0 else 0,
            "deep_engagement": metrics.get("scroll_90", 0)
        }

    def get_all_page_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics for all tracked pages."""
        # Find all page metric keys
        pattern = self._key("page_metrics", "*")
        keys = self.redis.keys(pattern)

        metrics = []
        for key in keys:
            # Extract page path from key (data is already decoded)
            page = key.split(":", 2)[-1]
            metrics.append(self.get_page_metrics(page))

        # Sort by views descending
        metrics.sort(key=lambda x: x["views"], reverse=True)
        return metrics

    # ========================================================================
    # ANALYTICS & REPORTING
    # ========================================================================

    def get_daily_unique_visitors(self, date: str = None) -> int:
        """
        Get unique visitor count for a specific date.

        Args:
            date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            Number of unique sessions
        """
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        key = self._key("daily_sessions", date)
        return self.redis.scard(key)

    def get_unique_visitors_range(self, start_date: str, end_date: str) -> int:
        """
        Get unique visitors across a date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Total unique sessions (deduplicated)
        """
        # Generate all dates in range
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        all_sessions = set()
        current = start

        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            key = self._key("daily_sessions", date_str)
            sessions = self.redis.smembers(key)
            # Data is already decoded (decode_responses=True)
            all_sessions.update(sessions)
            current += timedelta(days=1)

        return len(all_sessions)

    def get_hourly_events(self, date: str = None, hour: int = None) -> int:
        """
        Get event count for a specific hour.

        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            hour: Hour 0-23 (defaults to current hour)

        Returns:
            Number of events in that hour
        """
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        if hour is None:
            hour = datetime.utcnow().hour

        key = self._key("hourly_events", f"{date}:{hour:02d}")
        count = self.redis.get(key)
        return int(count) if count else 0

    def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get a comprehensive analytics summary.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with analytics data
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get unique visitors
        unique_visitors = self.get_unique_visitors_range(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

        # Get today's visitors
        today_visitors = self.get_daily_unique_visitors()

        # Get page metrics
        page_metrics = self.get_all_page_metrics()

        # Calculate total page views
        total_views = sum(p["views"] for p in page_metrics)

        # Get top pages
        top_pages = page_metrics[:10] if page_metrics else []

        return {
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "days": days
            },
            "visitors": {
                "total": unique_visitors,
                "today": today_visitors,
                "avg_per_day": round(unique_visitors / days, 1) if days > 0 else 0
            },
            "page_views": {
                "total": total_views,
                "avg_per_visitor": round(total_views / unique_visitors, 1) if unique_visitors > 0 else 0
            },
            "top_pages": top_pages,
            "all_pages": page_metrics
        }

    def get_user_journey(self, session_id: str) -> Dict[str, Any]:
        """
        Get the complete user journey for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with journey data and timeline
        """
        events = self.get_session_events(session_id)
        session = self.get_session(session_id)

        if not events:
            return {"session_id": session_id, "events": [], "pages": []}

        # Extract page views in order
        pages_visited = []
        for event in events:
            if event.get("event_type") == "page_view":
                pages_visited.append({
                    "page": event.get("page"),
                    "timestamp": event.get("timestamp"),
                    "referrer": event.get("referrer")
                })

        # Calculate session metrics
        first_event = events[0]
        last_event = events[-1]

        return {
            "session_id": session_id,
            "session_data": session,
            "first_seen": first_event.get("timestamp"),
            "last_seen": last_event.get("timestamp"),
            "pages_visited": len(pages_visited),
            "total_events": len(events),
            "journey": pages_visited,
            "events": events
        }

    # ========================================================================
    # DATA EXPORT & CLEANUP
    # ========================================================================

    def export_session_data(self, session_id: str) -> Dict[str, Any]:
        """
        Export all data for a session (for GDPR compliance).

        Args:
            session_id: Session identifier

        Returns:
            Complete session data including all events
        """
        return self.get_user_journey(session_id)

    def delete_session_data(self, session_id: str) -> bool:
        """
        Delete all data for a session (for GDPR right to deletion).

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        pipeline = self.redis.pipeline()

        # Delete session hash
        pipeline.delete(self._key("session", session_id))

        # Delete events list
        pipeline.delete(self._key("events", session_id))

        # Remove from daily session sets (approximate - we check last 90 days)
        for i in range(90):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            pipeline.srem(self._key("daily_sessions", date), session_id)

        pipeline.execute()
        return True

    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        Clean up data older than specified days.
        Note: This is a helper function. Redis TTL handles most cleanup automatically.

        Args:
            days_to_keep: Number of days of data to retain
        """
        # Redis TTL handles automatic cleanup
        # This function is here for manual cleanup if needed
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Could implement manual cleanup logic here if needed
        # For now, relying on Redis EXPIRE is sufficient
        pass
