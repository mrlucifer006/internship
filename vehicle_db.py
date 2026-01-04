import logging
import datetime
import math
from db import get_supabase_client
from pagination import PaginationResult

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
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error inserting vehicle: {e}")
        return False

def get_vehicle_by_reg_no(veh_reg_no):
    """Get a vehicle record by registration number."""
    try:
        response = supabase.table('vehicle').select("*").eq('veh_reg_no', veh_reg_no).execute()
        
        # Return first record as Dictionary (matching current behavior)
        if response.data and len(response.data) > 0:
            return response.data[0] 
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting vehicle by reg no: {e}")
        return None

def get_vehicle_by_driver(driver_name):
    """Get all vehicles associated with a driver."""
    try:
        response = supabase.table('vehicle').select("*").eq('driver_name', driver_name).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error getting vehicles by driver: {e}")
        return []

def get_all_vehicles():
    """Get all vehicle records."""
    try:
        # Order by time descending
        response = supabase.table('vehicle').select("*").order('time', desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error getting all vehicles: {e}")
        return []

def get_vehicles_paginated(page: int = 1, per_page: int = 50, search: str = None) -> PaginationResult:
    """
    Get vehicle records with pagination.
    """
    try:
        # Start building the query
        query = supabase.table('vehicle').select("*", count='exact')
        
        if search:
            # Using 'ilike' for case-insensitive search on multiple columns
            # Supabase 'or' filter syntax: "column.ilike.%search%,other.ilike.%search%"
            search_pattern = f"%{search}%"
            # NOTE: Supabase filter syntax for OR across columns can be tricky.
            # Using explicit filter string
            or_filter = f"driver_name.ilike.*{search}*,veh_reg_no.ilike.*{search}*,destination.ilike.*{search}*"
            query = query.or_(or_filter)
            
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page - 1 # Supabase range is inclusive
        
        response = query.order('time', desc=True).range(start, end).execute()
        
        data = response.data
        total = response.count if response.count is not None else 0
        
        total_pages = math.ceil(total / per_page) if total else 1
        has_next = page < total_pages
        has_prev = page > 1
        
        return PaginationResult(
            data=data,
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
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

def update_vehicle(veh_reg_no, data):
    """Update a vehicle record."""
    try:
        payload = {
            "driver_name": data.get("driver_name"),
            "vehicle_img": data.get("vehicle_img"),
            "destination": data.get("destination"),
            "time": data.get("time")
        }
        # Filter out None values just in case we don't want to unset them? 
        # Usually updates are explicit. Let's keep it simple.
        
        response = supabase.table('vehicle').update(payload).eq('veh_reg_no', veh_reg_no).execute()
        
        if response.data:
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
        response = supabase.table('vehicle').delete().eq('veh_reg_no', veh_reg_no).execute()
        if response.data:
            return True
        else:
            logger.warning(f"No vehicle found with registration number: {veh_reg_no}")
            return False
    except Exception as e:
        logger.error(f"Error deleting vehicle: {e}")
        return False

def search_vehicles_by_destination(destination):
    """Search vehicles by destination."""
    try:
        response = supabase.table('vehicle').select("*").ilike('destination', f"%{destination}%").execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error searching vehicles: {e}")
        return []
