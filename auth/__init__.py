"""
Supabase Authentication & Workspace Management Module
======================================================

Complete standalone module for:
- OAuth login (Google, GitHub, Apple)
- User management
- Workspace CRUD operations
- Q&A functionality
- PDF export

Ready to plug into Flask app!
"""

import os
from flask import Flask

# Import blueprints from route modules
from .oauth_routes import auth_bp
from .workspace_routes import workspace_bp, pages_bp

# Import Q&A and PDF routes (they register on workspace_bp)
from . import qa_routes  # noqa: F401
from . import pdf_routes  # noqa: F401


def register_blueprints(app: Flask):
    """Register all auth and workspace blueprints with Flask app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(workspace_bp)
    app.register_blueprint(pages_bp)


def init_app(app: Flask):
    """
    Initialize Supabase auth with Flask app

    This function:
    - Registers all auth-related blueprints
    - Sets up Supabase integration
    - Configures session management
    """
    # Set secret key for sessions
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')

    # Register blueprints
    register_blueprints(app)

    print("OK: Supabase Auth module initialized")


# Re-export commonly used items for convenience
from .decorators import require_auth  # noqa: E402
from .config import Config  # noqa: E402
from .utils import get_current_user_id, get_current_user  # noqa: E402
from .exceptions import (  # noqa: E402
    AuthError,
    LimitExceededError,
    WorkspaceNotFoundError,
    UnauthorizedError
)

__all__ = [
    'init_app',
    'require_auth',
    'Config',
    'get_current_user_id',
    'get_current_user',
    'AuthError',
    'LimitExceededError',
    'WorkspaceNotFoundError',
    'UnauthorizedError',
]
