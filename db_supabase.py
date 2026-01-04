import os
from supabase import create_client, Client

# Initialize Supabase Client
url: str = os.environ.get("SUPABASE_URL", "https://ssllkfvjipffuswektaq.supabase.co")
key: str = os.environ.get("SUPABASE_KEY", "sb_publishable_2hF1hYUU7dxfbvVdBMRWXg_82m86KZJ")
supabase: Client = create_client(url, key)

def get_supabase_client() -> Client:
    return supabase
