import sqlite3
import os

DB_NAME = 'vehicle.db'

def get_db_connection():
    """Get a connection to the vehicle database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    """Create the vehicle table if it doesn't exist."""
    try:
        conn = get_db_connection()
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vehicle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    driver_name TEXT NOT NULL,
                    veh_reg_no TEXT NOT NULL UNIQUE,
                    vehicle_img TEXT,
                    destination TEXT NOT NULL,
                    driver_phone TEXT,
                    origin TEXT,
                    time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migration check: Add columns if they don't exist (for existing DBs)
            cursor = conn.execute("PRAGMA table_info(vehicle)")
            columns = [info['name'] for info in cursor.fetchall()]
            
            if 'driver_phone' not in columns:
                try:
                    conn.execute("ALTER TABLE vehicle ADD COLUMN driver_phone TEXT")
                    print("Added driver_phone column to vehicle table")
                except Exception as e:
                    print(f"Error adding driver_phone column: {e}")
                    
            if 'origin' not in columns:
                try:
                    conn.execute("ALTER TABLE vehicle ADD COLUMN origin TEXT")
                    print("Added origin column to vehicle table")
                except Exception as e:
                    print(f"Error adding origin column: {e}")

        return True
    except Exception as e:
        print(f"Error creating/updating table: {e}")
        return False
    finally:
        conn.close()

def insert_vehicle(data):
    """Insert a new vehicle record into the database."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO vehicle (driver_name, veh_reg_no, vehicle_img, destination, time, driver_phone, origin) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data["driver_name"],
                data["veh_reg_no"],
                data.get("vehicle_img"),  # Optional field
                data["destination"],
                data.get("time"),  # If not provided, will use default CURRENT_TIMESTAMP
                data.get("driver_phone"),
                data.get("origin")
            ))
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Vehicle with registration number {data['veh_reg_no']} already exists.")
        return False
    except Exception as e:
        print(f"Error inserting vehicle: {e}")
        return False
    finally:
        conn.close()

def get_vehicle_by_reg_no(veh_reg_no):
    """Get a vehicle record by registration number."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT * FROM vehicle WHERE veh_reg_no = ?", (veh_reg_no,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        else:
            return None
    except Exception as e:
        print(f"Error getting vehicle by reg no: {e}")
        return None
    finally:
        conn.close()

def get_vehicle_by_driver(driver_name):
    """Get all vehicles associated with a driver."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT * FROM vehicle WHERE driver_name = ?", (driver_name,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error getting vehicles by driver: {e}")
        return []
    finally:
        conn.close()

def get_all_vehicles():
    """Get all vehicle records."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT * FROM vehicle ORDER BY time DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error getting all vehicles: {e}")
        return []
    finally:
        conn.close()

def update_vehicle(veh_reg_no, data):
    """Update a vehicle record."""
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute("""
                UPDATE vehicle 
                SET driver_name = ?, vehicle_img = ?, destination = ?, time = ?
                WHERE veh_reg_no = ?
            """, (
                data.get("driver_name"),
                data.get("vehicle_img"),
                data.get("destination"),
                data.get("time"),
                veh_reg_no
            ))
            if cursor.rowcount == 0:
                print(f"No vehicle found with registration number: {veh_reg_no}")
                return False
        return True
    except Exception as e:
        print(f"Error updating vehicle: {e}")
        return False
    finally:
        conn.close()

def delete_vehicle(veh_reg_no):
    """Delete a vehicle record by registration number."""
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute("DELETE FROM vehicle WHERE veh_reg_no = ?", (veh_reg_no,))
            if cursor.rowcount == 0:
                print(f"No vehicle found with registration number: {veh_reg_no}")
                return False
        return True
    except Exception as e:
        print(f"Error deleting vehicle: {e}")
        return False
    finally:
        conn.close()

def search_vehicles_by_destination(destination):
    """Search vehicles by destination."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT * FROM vehicle WHERE destination LIKE ?", (f"%{destination}%",))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error searching vehicles: {e}")
        return []
    finally:
        conn.close()


# Initialize the table when the module is imported
create_table()
