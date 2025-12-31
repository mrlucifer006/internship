"""
Launcher script for the Visitor Management System executable.
This script is the entry point for PyInstaller.
"""
import sys
import os
import webbrowser
import time
from threading import Timer

def open_browser():
    """Open browser after a short delay to allow Flask to start."""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    # Import app after path setup for frozen executable
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = sys._MEIPASS
        
        # Add the bundle directory to the path
        sys.path.insert(0, application_path)
        
        # Import Flask app
        from app import app
        
        # Set template and static folders for bundled app
        app.template_folder = os.path.join(application_path, 'templates')
        app.static_folder = os.path.join(application_path, 'static')
        
        # Ensure database files are accessible
        os.chdir(os.path.dirname(sys.executable))
    else:
        # Running as normal Python script
        from app import app
    
    # Open browser automatically
    Timer(1, open_browser).start()
    
    # Run Flask app
    print("=" * 60)
    print("Visitor Management System")
    print("=" * 60)
    print(f"Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nServer stopped.")
