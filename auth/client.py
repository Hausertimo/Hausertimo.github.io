"""
Supabase client initialization
"""

from supabase import create_client, Client
from .config import Config


# Initialize Supabase client with service key for admin operations
supabase: Client = create_client(
    Config.SUPABASE_URL,
    Config.SUPABASE_SERVICE_KEY
)
