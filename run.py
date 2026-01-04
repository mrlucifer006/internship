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
    
    # Initialize Application Logic (DB tables, backups, etc.)
    try:
        app.initialize_application()
    except AttributeError:
        # Fallback if app doesn't have the method (during dev) or circular import issues
        print("Warning: initialize_application not found on app object.")
    
    # Run Flask app
    print("=" * 60)
    print("Visitor Management System")
    print("=" * 60)
    print(f"Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # User requested "Gunicorn" (Production Server).
        # On Windows, 'Waitress' is the recommended WSGI server equivalent to Gunicorn.
        from waitress import serve
        print("Using Waitress Production Server (Windows-compatible alternative to Gunicorn)")
        serve(app, host='0.0.0.0', port=5000, threads=6)
    except ImportError:
        print("Waitress not installed. Falling back to Flask Development Server.")
        print("To use Production Server: pip install waitress")
        try:
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        except KeyboardInterrupt:
            pass
    except KeyboardInterrupt:
        print("\nServer stopped.")
