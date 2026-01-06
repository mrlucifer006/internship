"""
Launcher script for the Visitor Management System executable.
This script is the entry point for PyInstaller.
"""
import sys
import os
import threading
import webview
import time

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
        
        serve(app, host='0.0.0.0', port=5000, threads=threads_count)
    except ImportError:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Server Discovery / Failover Logic
    try:
        from server_discovery import discover_server
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
    
    # Create the native window
    # Connect to the discovered IP (Local or Remote)
    webview.create_window(
        'Visitor Management System', 
        f'http://{ip_address}:5000',
        width=1280,
        height=720,
        resizable=True,
        maximized=True
    )
    
    # Start the GUI loop
    webview.start()

