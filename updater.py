import os
import sys
import requests
import subprocess
from packaging import version
from config import Config

# Configuration
# We use the Config class to get version, but we need raw env vars for Supabase 
# because we might not want to initialize the full app context just for checking updates.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
CURRENT_VERSION = Config.CURRENT_VERSION

def download_from_google_drive(file_id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={'id': file_id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    print(f" [Updater]: Download complete: {destination}")

def check_for_updates():
    """
    Checks for updates against the Supabase database.
    If an update is found, it downloads it and restarts the application.
    If no update, it returns safely to allow normal startup.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print(" [Updater]: Supabase URL or KEY missing. Skipping update check.")
        return

    # Construct the endpoint URL using the user's snippet logic
    # URL: https://your-project.supabase.co/rest/v1/app_updates?select=*&order=id.desc&limit=1
    update_url = f"{SUPABASE_URL}/rest/v1/app_updates?select=*&order=id.desc&limit=1"
    headers = {
        "apikey": SUPABASE_KEY, 
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    print(f" [Updater]: Checking for updates... (Current: {CURRENT_VERSION})")

    try:
        response = requests.get(update_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f" [Updater]: Failed to fetch updates. Status: {response.status_code}")
            return

        data = response.json()
        if not data:
            print(" [Updater]: No update info found in database.")
            return

        server_version = data[0]['version']
        google_drive_id = data[0]['download_url'] # This is now the File ID

        print(f" [Updater]: Server Version: {server_version}")

        if version.parse(server_version) > version.parse(CURRENT_VERSION):
            print(" [Updater]: New update found! Downloading from Google Drive...")
            perform_update(google_drive_id)
        else:
            print(" [Updater]: You are on the latest version.")
            # Normal return; let the app start
            return

    except Exception as e:
        print(f" [Updater]: Update check failed: {e}")
        # On error, just return and let app start
        return

def perform_update(file_id):
    """
    Downloads the new executable from Google Drive and creates a batch script to swap it.
    """
    try:
        # 1. Download New File
        new_filename = "update_temp.exe"
        download_from_google_drive(file_id, new_filename)
        
        # 2. Identify Current Executable
        if getattr(sys, 'frozen', False):
            current_app = sys.executable
        else:
            # If running as script, we can't really "update" the script runner (python.exe)
            print(" [Updater]: Running in non-frozen mode. Update downloaded as 'update_temp.exe' but won't replace source.")
            return

        app_name = os.path.basename(current_app)
        app_dir = os.path.dirname(current_app)
        
        # Ensure we are working in the app directory
        # (Though run.py already changes cwd to sys.executable dir usually)
        
        # 3. Create Batch Script
        # We need to handle paths carefully if they have spaces
        bat_script = f"""
@echo off
timeout /t 2 /nobreak > NUL
del "{app_name}"
if exist "{app_name}" goto fail
rename "{new_filename}" "{app_name}"
start "" "{app_name}"
del "%~f0"
exit

:fail
echo Failed to delete original file.
pause
"""
        
        bat_path = os.path.join(app_dir, "updater.bat")
        with open(bat_path, "w") as f:
            f.write(bat_script)

        print(" [Updater]: Restarting to apply updates...")
        
        # 4. Execute Batch and Exit
        subprocess.Popen(bat_path, shell=True, cwd=app_dir)
        sys.exit(0)

    except Exception as e:
        print(f" [Updater]: Failed to perform update: {e}")
        # Don't exit; let user could still potentially use the old app
