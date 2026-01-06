import socket
import logging
import requests
import time
from datetime import datetime
from db_supabase import get_supabase_client

logger = logging.getLogger(__name__)

def get_local_ip():
    """Get the local machine's IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually connect, just determines route
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def check_server_health(ip, port=5000):
    """
    Check if the server at the given IP is reachable and running Flask.
    Returns True if healthy.
    """
    try:
        url = f"http://{ip}:{port}/check_updates" 
        # Use a short timeout to fail fast
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

def discover_server():
    """
    Determines if this instance should act as Server or Client.
    Checks 'employee' table for any active user connecting as 'Server'.
    """
    supabase = get_supabase_client()
    local_ip = get_local_ip()
    
    try:
        # 1. Look for any Online employee who is acting as Server
        response = supabase.table('employee').select('ip_address') \
            .eq('connection_mode', 'Server') \
            .eq('status', 1) \
            .execute()
        
        server_ip = None
        if response.data:
            # Check candidate IPs
            for row in response.data:
                candidate_ip = row.get('ip_address')
                if not candidate_ip: continue
                
                # If the registered server is ME, then I am Server
                if candidate_ip == local_ip:
                    logger.info("Found myself listed as Active Server.")
                    return 'SERVER', local_ip
                
                # Check if remote server is healthy
                if check_server_health(candidate_ip):
                    logger.info(f"Found active Remote Server at {candidate_ip}. Acting as CLIENT.")
                    return 'CLIENT', candidate_ip
                else:
                    logger.warning(f"Registered Server at {candidate_ip} is unreachable.")
        
        # 2. No active/healthy server found -> I become Server
        logger.info("No active server found. Starting Local Server.")
        return 'SERVER', local_ip

    except Exception as e:
        logger.error(f"Server Discovery Failed: {e}")
        # Fallback to Server Mode
        return 'SERVER', local_ip
