import vehicle_db
import sqlite3
import os

def verify_db_schema():
    print("Verifying database schema...")
    
    # Ensure update runs
    vehicle_db.create_table()
    
    conn = sqlite3.connect(vehicle_db.DB_NAME)
    cursor = conn.execute("PRAGMA table_info(vehicle)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    
    print(f"Columns found: {columns}")
    
    required_columns = ['driver_phone', 'origin']
    missing = [col for col in required_columns if col not in columns]
    
    if missing:
        print(f"❌ Missing columns: {missing}")
        exit(1)
    else:
        print("✅ Schema verification successful: All columns present.")
        exit(0)

if __name__ == "__main__":
    verify_db_schema()
