import os
import logging
from db_supabase import get_supabase_client

logger = logging.getLogger(__name__)

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

