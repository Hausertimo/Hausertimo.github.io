"""
Configuration for Supabase and app limits
"""

import os


class Config:
    """Configuration for Supabase and app limits"""

    # Supabase credentials (from environment variables)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

    # Workspace limits (None = unlimited, ready to enforce later)
    MAX_WORKSPACES_PER_USER = None  # Set to 50 when ready
    MAX_QA_PER_WORKSPACE = None     # Set to 100 when ready
    WARN_AT_WORKSPACE_COUNT = 45    # Show warning at 45/50
    WARN_AT_QA_COUNT = 90           # Show warning at 90/100

    # OAuth redirect URLs
    SITE_URL = os.getenv('SITE_URL', 'https://normscout.ch')

    # Session config
    SESSION_COOKIE_NAME = 'sb_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # Only over HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
