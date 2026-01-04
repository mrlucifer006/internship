import sqlite3
import logging
from db import get_supabase_client

logger = logging.getLogger(__name__)

def get_db_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect('local_cache.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database and create tables if they don't exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Read schema from file
        with open('schema.sql', 'r') as f:
            schema = f.read()
        
        cursor.executescript(schema)
        conn.commit()
        conn.close()
        logger.info("Local database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing local database: {e}")

def sync_data_from_supabase():
    """Fetch data from Supabase and sync it with the local SQLite database."""
    try:
        supabase = get_supabase_client()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Sync employees
        employees = supabase.table('employee').select('*').execute().data
        if employees:
            cursor.execute("DELETE FROM employee")
            for emp in employees:
                cursor.execute(
                    "INSERT INTO employee (id, name, phone, login_id, password, Auth_level, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (emp['id'], emp['name'], emp['phone'], emp['login_id'], emp['password'], emp['Auth_level'], emp['status'], emp['created_at'])
                )

        # Sync visitors
        visitors = supabase.table('visitors').select('*').execute().data
        if visitors:
            cursor.execute("DELETE FROM visitors")
            for v in visitors:
                cursor.execute(
                    "INSERT INTO visitors (id, name, phone, person_to_visit, reason, has_vehicle, vehicle_number, entry_time, exit_time, status, denial_reason, updated_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (v['id'], v['name'], v['phone'], v['person_to_visit'], v['reason'], v['has_vehicle'], v['vehicle_number'], v['entry_time'], v['exit_time'], v['status'], v['denial_reason'], v['updated_at'], v['created_at'])
                )

        # Sync vehicles
        vehicles = supabase.table('vehicle').select('*').execute().data
        if vehicles:
            cursor.execute("DELETE FROM vehicle")
            for v in vehicles:
                cursor.execute(
                    "INSERT INTO vehicle (id, driver_name, veh_reg_no, vehicle_img, destination, \"time\", driver_phone, origin, purchase_no, entry_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (v['id'], v['driver_name'], v['veh_reg_no'], v['vehicle_img'], v['destination'], v['time'], v['driver_phone'], v['origin'], v['purchase_no'], v['entry_type'], v['created_at'])
                )

        conn.commit()
        conn.close()
        logger.info("Local database synced with Supabase.")
    except Exception as e:
        logger.error(f"Error syncing data from Supabase: {e}")

if __name__ == '__main__':
    init_db()
    sync_data_from_supabase()
