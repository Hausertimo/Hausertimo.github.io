"""
Authentication decorators for route protection
"""

from functools import wraps
from flask import request, jsonify
from .client import supabase
from .config import Config


def require_auth(f):
    """
    Decorator to protect routes - requires valid Supabase JWT token

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user_id = get_current_user_id()
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header or cookie
        token = None

        # Try Authorization header first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')

        # Fall back to cookie
        if not token:
            token = request.cookies.get(Config.SESSION_COOKIE_NAME)

        if not token:
            return jsonify({"error": "Not authenticated"}), 401

        try:
            # Verify token with Supabase
            user = supabase.auth.get_user(token)
            if not user or not user.user:
                return jsonify({"error": "Invalid token"}), 401

            # Store user info in request context
            request.current_user = user.user

        except Exception as e:
            return jsonify({"error": f"Authentication failed: {str(e)}"}), 401

        return f(*args, **kwargs)

    return decorated_function
