"""
Launcher script for the Visitor Management System executable.
This script is the entry point for PyInstaller.
"""
import sys
import os
import threading
import webview
import time
import subprocess
import re
import atexit

# Import Flask app and initialization
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
    sys.path.insert(0, application_path)
    
    from app import app, initialize_application
    
    # Set template and static folders for bundled app
    app.template_folder = os.path.join(application_path, 'templates')
    app.static_folder = os.path.join(application_path, 'static')
    
    # Ensure database files are accessible
    os.chdir(os.path.dirname(sys.executable))
else:
    # Running as normal Python script
    from app import app, initialize_application

def start_cloudflared_tunnel(port=5000):
    """Starts a cloudflared tunnel and returns the public URL."""
    try:
        print(f"Starting Cloudflare Tunnel on port {port}...")
        
        # Determine executable name
        cf_exe = 'cloudflared'
        
        # Check current directory for common windows name
        if os.path.exists('cloudflared-windows-amd64.exe'):
            cf_exe = os.path.abspath('cloudflared-windows-amd64.exe')
        elif os.path.exists('cloudflared.exe'):
             cf_exe = os.path.abspath('cloudflared.exe')
        
        # Check if cloudflared is accessible
        try:
            print(f"Using Cloudflare Executable: {cf_exe}")
            subprocess.run([cf_exe, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
             print(f"ERROR: '{cf_exe}' executable not found or failed. Please download it from Cloudflare.")
             return None

        # Start the tunnel
        process = subprocess.Popen(
            [cf_exe, 'tunnel', '--url', f'http://localhost:{port}'],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,            # Line buffered
            encoding='utf-8'      # Explicit encoding
        )
        
        # Register cleanup
        atexit.register(lambda: process.terminate())
        
        # Scan stderr for the URL (it usually appears within a few seconds)
        # We read line by line.
        public_url = None
        timeout = 20
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # We use readline() which blocks, but cloudflared outputs frequently at start
            line = process.stderr.readline()
            if not line:
                if process.poll() is not None:
                     print("Cloudflared process exited unexpectedly.")
                     break
                continue
                
            # print(f"[CF Log]: {line.strip()}") # Optional: debug logs
            
            # Look for the URL
            if "trycloudflare.com" in line:
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if match:
                    public_url = match.group(0)
                    print(f" * Cloudflare Tunnel URL: {public_url}")
                    # Launch a thread to keep draining stderr so buffer doesn't fill
                    def drain_stream(stream):
                        for _ in stream: pass
                    threading.Thread(target=drain_stream, args=(process.stderr,), daemon=True).start()
                    break
        
        if not public_url:
            print("Timed out waiting for Cloudflare URL.")
            process.terminate()
            
        return public_url
            
    except Exception as e:
        print(f"Failed to start Cloudflare Tunnel: {e}")
        return None

def start_server():
    """Starts the Flask server."""
    # Initialize Application Logic (DB tables, backups, etc.)
    try:
        initialize_application()
    except Exception as e:
        print(f"Error during application initialization: {e}")

    # Run Server
    try:
        from waitress import serve
        import multiprocessing
        
        # Optimize thread count for concurrency (I/O bound)
        # Using cpu_count() * 2 + 1 is a standard recommendation for WSGI servers
        threads_count = multiprocessing.cpu_count() * 2 + 1
        print(f"Starting Waitress Server with {threads_count} threads...")

        # Start Cloudflare Tunnel if enabled
        if app.config.get('ENABLE_TUNNEL'):
            try:
                public_url = start_cloudflared_tunnel(port=5000)
                if public_url:
                    app.config['PUBLIC_URL'] = public_url
            except Exception as e:
                print(f" * Tunnel Error: {e}")
        
        serve(app, host='0.0.0.0', port=5000, threads=threads_count)
    except ImportError:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Server Discovery / Failover Logic
    try:
        from server_discovery import discover_server, cleanup_stale_sessions
        
        # 0. Clean up any previous mess from THIS machine
        cleanup_stale_sessions()
        
        mode, ip_address = discover_server()
        print(f"Starting in {mode} mode. Target IP: {ip_address}")
    except Exception as e:
        print(f"Discovery failed (`{e}`). Fallback to Local Server.")
        mode = 'SERVER'
        from server_discovery import get_local_ip
        ip_address = get_local_ip()

    # Start Flask Server ONLY if acting as SERVER
    if mode == 'SERVER':
        # Start the server in a separate thread
        t = threading.Thread(target=start_server)
        t.daemon = True
        t.start()
        
        # Give server a moment to start
        time.sleep(1) 
        
        # REGISTER CLEANUP: When Server exits, clear ALL client sessions
        from employee_db import reset_all_employee_statuses
        atexit.register(reset_all_employee_statuses)
        print(" [Server Mode]: Registered global session cleanup on exit.")
    
    # Create the native window
    # Create the native window
    # Connect to the discovered IP (Local or Remote)
    if ip_address.startswith('http'):
        target_url = ip_address
    else:
        target_url = f'http://{ip_address}:5000'

    webview.create_window(
        'Visitor Management System', 
        target_url,
        width=1280,
        height=720,
        resizable=True,
        maximized=True
    )
    
    # Start the GUI loop
    webview.start()

