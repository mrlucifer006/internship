import sqlite3
import os
import logging
from pagination import paginate_query, PaginationResult, safe_db_connection

logger = logging.getLogger(__name__)

DB_NAME = 'vehicle.db'

def get_db_connection():
    """Get a connection to the vehicle database with WAL mode for better concurrency."""
    conn = sqlite3.connect(DB_NAME, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def create_table():
    """Create the vehicle table if it doesn't exist."""
    try:
        conn = get_db_connection()
        with conn:
            # Check if table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicle'")
            table_exists = cursor.fetchone()

            if not table_exists:
                conn.execute("""
                    CREATE TABLE vehicle (
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
            else:
                # Migration check: Add columns if they don't exist
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

                if 'purchase_no' not in columns:
                    try:
                        conn.execute("ALTER TABLE vehicle ADD COLUMN purchase_no TEXT")
                        print("Added purchase_no column to vehicle table")
                    except Exception as e:
                        print(f"Error adding purchase_no column: {e}")
                        
                if 'entry_type' not in columns:
                    try:
                        conn.execute("ALTER TABLE vehicle ADD COLUMN entry_type TEXT DEFAULT 'Entry'")
                        print("Added entry_type column to vehicle table")
                    except Exception as e:
                        print(f"Error adding entry_type column: {e}")
                        
                # Check for UNIQUE constraint on veh_reg_no by attempting to insert a duplicate
                # If it fails, we need to migrate to remove the UNIQUE constraint
                # Ideally, we check the schema, but SQLite schema parsing is tricky.
                # A robust way is to rename the table and recreate it without UNIQUE if we suspect it's old.
                # For this internship demo, we will attempt a "Migration v2" strategy if needed.
                # However, since we can't easily check constraints, let's assume if 'purchase_no' was just added, 
                # we might still have the old schema. 
                # THE BEST APPROACH for SQLite to remove a constraint is:
                # 1. Rename table to vehicle_old
                # 2. Create new table without constraint
                # 3. Copy data
                # 4. Drop old table
                
                # Let's do a safe migration check: 
                # If we can't insert a duplicate, we fix it. But that's runtime.
                # Let's just do the migration if we haven't done it yet.
                # We can use a special flag column or just check if we can insert duplicates.
                pass 

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
                INSERT INTO vehicle (driver_name, veh_reg_no, vehicle_img, destination, time, driver_phone, origin, purchase_no, entry_type) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["driver_name"],
                data["veh_reg_no"],
                data.get("vehicle_img"),  # Optional field
                data["destination"],
                data.get("time"),  # If not provided, will use default CURRENT_TIMESTAMP
                data.get("driver_phone"),
                data.get("origin"),
                data.get("purchase_no"),
                data.get("entry_type", "Entry") # Default to Entry
            ))
        return True
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


def get_vehicles_paginated(page: int = 1, per_page: int = 50, search: str = None) -> PaginationResult:
    """
    Get vehicle records with pagination.
    
    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        search: Optional search term for driver name or vehicle number
        
    Returns:
        PaginationResult with data and pagination metadata
    """
    conn = get_db_connection()
    try:
        base_query = "SELECT * FROM vehicle"
        count_query = "SELECT COUNT(*) FROM vehicle"
        params = ()
        
        # Add search filter if provided
        if search:
            search_pattern = f"%{search}%"
            base_query += " WHERE driver_name LIKE ? OR veh_reg_no LIKE ? OR destination LIKE ?"
            count_query += " WHERE driver_name LIKE ? OR veh_reg_no LIKE ? OR destination LIKE ?"
            params = (search_pattern, search_pattern, search_pattern)
        
        base_query += " ORDER BY time DESC"
        
        result = paginate_query(conn, base_query, count_query, params, page, per_page)
        return result
        
    except Exception as e:
        logger.error(f"Error getting paginated vehicles: {e}")
        return PaginationResult(
            data=[],
            page=1,
            per_page=per_page,
            total=0,
            total_pages=1,
            has_next=False,
            has_prev=False
        )
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
