import sqlite3
import threading
import logging
from db_backup import DatabaseBackup

import os
import sys

def get_base_path():
    """Get the persistent base path (compatible with PyInstaller and script)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# Ensure instance folder exists
base_dir = get_base_path()
instance_dir = os.path.join(base_dir, 'instance')
os.makedirs(instance_dir, exist_ok=True)

# Set absolute DB path
DB_NAME = os.path.join(instance_dir, "visitor_management.db")
print(f"DEBUG: Database path set to: {DB_NAME}")

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the unified database."""
    conn = sqlite3.connect(DB_NAME, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def trigger_backup(reason=None):
    """Triggers a database backup in a background thread."""
    if reason:
        logger.info(f"Backup triggered due to: {reason}")
        
    def run_backup():
        try:
            # Re-instantiate locally to avoid thread sharing issues if any
            # Note: We aren't passing a secret key here, so it stays unencrypted for auto-backups 
            # unless we decide to hardcode/config it. For now, plain backups.
            backup_manager = DatabaseBackup(db_path=DB_NAME)
            path = backup_manager.create_backup()
            
            # Cleanup old backups automatically to save space
            backup_manager.cleanup_old_backups(keep_count=20)
            
        except Exception as e:
            logger.error(f"Auto-backup failed: {e}")

    # Run in thread to not block the main request
    threading.Thread(target=run_backup).start()

def init_db(app=None):
    """Initialize the unified database with all tables."""
    conn = get_db_connection()
    try:
        with conn:
            # 1. Visitor Table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS visitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_number TEXT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    person_to_visit TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    has_vehicle INTEGER DEFAULT 0,
                    vehicle_number TEXT,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT,
                    approval_status TEXT DEFAULT 'Approved',
                    updated_at TEXT,
                    denial_reason TEXT
                )
            ''')
            
            # 2. Employee Table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS employee (
                    name TEXT NOT NULL, 
                    phone TEXT NOT NULL, 
                    login_id TEXT NOT NULL, 
                    password TEXT NOT NULL, 
                    Auth_level INT NOT NULL, 
                    status BOOLEAN NOT NULL DEFAULT 0
                )
            ''')
            
            # 3. Notifications Table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    host_login_id TEXT NOT NULL, 
                    visitor_name TEXT NOT NULL, 
                    reason TEXT NOT NULL, 
                    visitor_id INTEGER, 
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                    is_read BOOLEAN DEFAULT 0
                )
            ''')
            
            # 4. Vehicle Table
            # Create if not exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vehicle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT NOT NULL,
                    veh_reg_no TEXT NOT NULL,
                    vehicle_img TEXT,
                    destination TEXT NOT NULL,
                    driver_phone TEXT,
                    origin TEXT,
                    purchase_no TEXT,
                    entry_type TEXT DEFAULT 'Entry',
                    time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migrations (ensure columns exist if updating from old schema)
            # Check for vehicle columns
            cursor = conn.execute("PRAGMA table_info(vehicle)")
            columns = [info['name'] for info in cursor.fetchall()]

            if 'driver_phone' not in columns:
                conn.execute("ALTER TABLE vehicle ADD COLUMN driver_phone TEXT")
            if 'origin' not in columns:
                conn.execute("ALTER TABLE vehicle ADD COLUMN origin TEXT")
            if 'purchase_no' not in columns:
                conn.execute("ALTER TABLE vehicle ADD COLUMN purchase_no TEXT")
            if 'entry_type' not in columns:
                conn.execute("ALTER TABLE vehicle ADD COLUMN entry_type TEXT DEFAULT 'Entry'")

            # Check for visitors columns
            cursor = conn.execute("PRAGMA table_info(visitors)")
            v_columns = [info['name'] for info in cursor.fetchall()]
            
            if 'approval_status' not in v_columns:
                conn.execute("ALTER TABLE visitors ADD COLUMN approval_status TEXT DEFAULT 'Approved'")
            if 'updated_at' not in v_columns:
                conn.execute("ALTER TABLE visitors ADD COLUMN updated_at TEXT")
            if 'denial_reason' not in v_columns:
                conn.execute("ALTER TABLE visitors ADD COLUMN denial_reason TEXT")
                
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        print(f"CRITICAL ERROR: Database initialization failed: {e}")
    finally:
        conn.close()
        print("Database initialization check complete.")
