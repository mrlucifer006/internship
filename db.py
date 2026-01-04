import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Initialize Supabase Client
# NOTE: Replace these with your actual Supabase URL and Key
url: str = os.environ.get("SUPABASE_URL", "https://ssllkfvjipffuswektaq.supabase.co")
key: str = os.environ.get("SUPABASE_KEY", "sb_publishable_2hF1hYUU7dxfbvVdBMRWXg_82m86KZJ")

_supabase: Client = None

def get_supabase_client() -> Client:
    """Get the Supabase client instance."""
    global _supabase
    if _supabase is None:
        try:
            _supabase = create_client(url, key)
            logger.info("Supabase client initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise e
    return _supabase

def get_db_connection():
    """
    Deprecated: Shim for legacy code.
    Should be replaced calls with get_supabase_client().
    """
    return get_supabase_client()


def init_db(app=None):
    """
    Initialize/Check Supabase connection.
    Table creation should be handled via Supabase Dashboard or SQL Migrations.
    This function now checks if we can connect.
    """
    try:
        client = get_supabase_client()
        # Simple health check query (e.g., specific to your schema or generally)
        # Assuming 'visitors' table exists.
        client.table('visitors').select("id", count='exact').limit(1).execute()
        print("Supabase connection check successful.")
    except Exception as e:
        logger.error(f"Supabase connection check failed: {e}")
        print(f"CRITICAL ERROR: Supabase connection check failed: {e}")

