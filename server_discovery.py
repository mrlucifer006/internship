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
    
    Returns:
        tuple: (mode, ip_address)
        mode: 'SERVER' or 'CLIENT'
        ip_address: The IP to connect to (Local IP if Server, Remote IP if Client)
    """
    supabase = get_supabase_client()
    local_ip = get_local_ip()
    
    try:
        # 1. Fetch current server IP from DB
        response = supabase.table('app_config').select('value').eq('key', 'server_ip').execute()
        
        server_ip = ""
        if response.data and len(response.data) > 0:
            server_ip = response.data[0]['value']
            
        logger.info(f"Discovered Server IP in DB: '{server_ip}'")

        # 2. Logic to decide role
        should_be_server = False

        if not server_ip:
            # Case A: No IP registered -> I become Server
            logger.info("No Server IP found. taking ownership.")
            should_be_server = True
        elif server_ip == local_ip:
             # Case B: I am already the registered server -> I am Server
             logger.info("I am the registered server.")
             should_be_server = True
        else:
            # Case C: Remote IP exists. Check if it's alive.
            if check_server_health(server_ip):
                logger.info(f"Remote server {server_ip} is healthy. Acting as CLIENT.")
                return 'CLIENT', server_ip
            else:
                # Case D: Remote IP is registered but dead -> Failover -> I become Server
                logger.warning(f"Remote server {server_ip} is unreachable. Performing FAILOVER.")
                should_be_server = True
        
        # 3. If I am Server, update DB
        if should_be_server:
            try:
                # Upsert current IP
                payload = { 'key': 'server_ip', 'value': local_ip, 'updated_at': datetime.now().isoformat() }
                supabase.table('app_config').upsert(payload).execute()
                logger.info(f"Registered as MASTER SERVER with IP: {local_ip}")
            except Exception as e:
                logger.error(f"Failed to register server IP: {e}")
                # Proceed anyway, we can run locally
            
            return 'SERVER', local_ip

    except Exception as e:
        logger.error(f"Server Discovery Failed: {e}")
        # Fallback to Server Mode (Safest for standalone usage)
        return 'SERVER', local_ip
