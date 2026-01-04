import logging
import datetime
import math
from db import get_supabase_client
from pagination import PaginationResult
from cache_manager import (
    get_all_local_vehicles, get_paginated_local_vehicles,
    update_local_vehicle, remove_local_vehicle, get_db_connection
)

logger = logging.getLogger(__name__)

supabase = get_supabase_client()

def create_table():
    """Calculated from db.py now, but keeping stub for compatibility if imported."""
    pass

def insert_vehicle(data):
    """Insert a new vehicle record into the database."""
    try:
        # Prepare data for Supabase (handling optional fields)
        payload = {
            "driver_name": data.get("driver_name"),
            "veh_reg_no": data.get("veh_reg_no"),
            "vehicle_img": data.get("vehicle_img"),
            "destination": data.get("destination"),
            "time": data.get("time") if data.get("time") else datetime.datetime.now().isoformat(),
            "driver_phone": data.get("driver_phone"),
            "origin": data.get("origin"),
            "purchase_no": data.get("purchase_no"),
            "entry_type": data.get("entry_type", "Entry")
        }
        
        # Execute insert
        response = supabase.table('vehicle').insert(payload).execute()
        
        # Check if insert was successful (response.data should be populated)
        if response.data:
            update_local_vehicle(response.data[0])
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error inserting vehicle: {e}")
        return False

def get_vehicle_by_reg_no(veh_reg_no):
    """Get a vehicle record by registration number."""
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT * FROM vehicle WHERE veh_reg_no = ?', (veh_reg_no,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        logger.error(f"Error getting vehicle by reg no from cache: {e}")
        return None
    finally:
        conn.close()

def get_vehicle_by_driver(driver_name):
    """Get all vehicles associated with a driver."""
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT * FROM vehicle WHERE driver_name = ?', (driver_name,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting vehicles by driver from cache: {e}")
        return []
    finally:
        conn.close()

def get_all_vehicles():
    """Get all vehicle records."""
    return get_all_local_vehicles()

def get_vehicles_paginated(page: int = 1, per_page: int = 50, search: str = None) -> PaginationResult:
    """
    Get vehicle records with pagination.
    """
    result = get_paginated_local_vehicles(page, per_page, search)
    
    total = result['total']
    total_pages = math.ceil(total / per_page) if total else 1
    has_next = page < total_pages
    has_prev = page > 1
    
    return PaginationResult(
        data=result['data'],
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

def update_vehicle(veh_reg_no, data):
    """Update a vehicle record."""
    try:
        payload = {
            "driver_name": data.get("driver_name"),
            "vehicle_img": data.get("vehicle_img"),
            "destination": data.get("destination"),
            "time": data.get("time")
        }
        
        response = supabase.table('vehicle').update(payload).eq('veh_reg_no', veh_reg_no).execute()
        
        if response.data:
            update_local_vehicle(response.data[0])
            return True
        else:
            logger.warning(f"No vehicle found with registration number: {veh_reg_no}")
            return False
    except Exception as e:
        logger.error(f"Error updating vehicle: {e}")
        return False

def delete_vehicle(veh_reg_no):
    """Delete a vehicle record by registration number."""
    try:
        # Get id before deleting
        vehicle = get_vehicle_by_reg_no(veh_reg_no)
        if not vehicle:
            logger.warning(f"No vehicle found with registration number: {veh_reg_no}")
            return False

        response = supabase.table('vehicle').delete().eq('veh_reg_no', veh_reg_no).execute()
        if response.data:
            remove_local_vehicle(vehicle['id'])
            return True
        else:
            logger.warning(f"No vehicle found with registration number: {veh_reg_no}")
            return False
    except Exception as e:
        logger.error(f"Error deleting vehicle: {e}")
        return False

def search_vehicles_by_destination(destination):
    """Search vehicles by destination."""
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT * FROM vehicle WHERE destination LIKE ?', (f'%{destination}%',))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error searching vehicles from cache: {e}")
        return []
    finally:
        conn.close()
