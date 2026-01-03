import sqlite3
import os
import logging
from pagination import paginate_query, PaginationResult
from db import get_db_connection, trigger_backup

logger = logging.getLogger(__name__)

# NOTE: DB_NAME and table creation are now managed in db.py

def create_table():
    """Calculated from db.py now, but keeping stub for compatibility if imported."""
    # Logic moved to db.init_db()
    pass

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
            trigger_backup() # BACKUP TRIGGER
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
            else:
                 trigger_backup() # BACKUP TRIGGER
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
            else:
                 trigger_backup() # BACKUP TRIGGER
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


# Table creation is now handled by app initialization calling db.init_db()
# create_table() # Removed auto-call to avoid side effects on import, and its logic is empty now.

