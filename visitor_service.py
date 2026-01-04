from db import get_supabase_client
from pagination import PaginationResult
from datetime import datetime
import logging
import math
from cache_manager import (
    get_all_local_visitors, get_active_local_visitors, get_paginated_local_visitors,
    update_local_visitor, remove_local_visitor, get_db_connection
)

logger = logging.getLogger(__name__)

supabase = get_supabase_client()

def save_visitor(data):
    """
    Validates and saves visitor data.
    """
    errors = []
    
    host_name = data.get("name")
    phone = data.get("Number")
    visitor_name = data.get("V_name")
    reason = data.get("reason")
    vehicle = data.get("vehicle") 
    vehicle_number = data.get("vehicle_number")

    if not host_name: errors.append("Host name is required.")
    if not phone: errors.append("Phone number is required.")
    if not visitor_name: errors.append("Visitor name is required.")
    if not reason: errors.append("Reason is required.")

    has_vehicle = 1 if vehicle else 0
    if has_vehicle and not vehicle_number:
         pass 

    if errors:
        return {"success": False, "errors": errors}

    try:
        # Simple duplicate check against local cache
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM visitors WHERE phone = ? AND name = ? AND exit_time IS NULL AND status != -1", (phone, visitor_name))
        if cursor.fetchone():
            return {"success": False, "errors": ["Visitor already checked in."]}

        # Default status is 'Pending'
        status = 0
        
        payload = {
            "name": visitor_name,
            "phone": phone,
            "person_to_visit": host_name,
            "reason": reason,
            "has_vehicle": has_vehicle,
            "vehicle_number": vehicle_number,
            "entry_time": datetime.now().isoformat(),
            "status": status, 
            "updated_at": datetime.now().isoformat()
        }

        response = supabase.table('visitors').insert(payload).execute()
        
        if response.data:
            visitor_id = response.data[0]['id']
            update_local_visitor(response.data[0])
            return {"success": True, "message": "Visitor registered successfully.", "visitor_id": visitor_id}
        else:
             return {"success": False, "errors": ["Database insert failed."]}

    except Exception as e:
        logger.error(f"Error saving visitor: {e}")
        return {"success": False, "errors": [str(e)]}

def update_visitor_status(visitor_id, status, denial_reason=None):
    """
    Updates the approval status of a visitor.
    - status: 1 for Approved, -1 for Denied
    - denial_reason: Optional reason for denial
    """
    if status not in [1, -1]:
        return {"success": False, "errors": ["Invalid status value."]}

    try:
        payload = {
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        if status == -1:
            payload["denial_reason"] = denial_reason

        response = supabase.table('visitors').update(payload).eq('id', visitor_id).execute()
        
        if response.data:
            update_local_visitor(response.data[0])
            return {"success": True, "message": "Visitor status updated."}
        else:
            return {"success": False, "errors": ["Failed to update visitor status."]}
            
    except Exception as e:
        logger.error(f"Error updating visitor status: {e}")
        return {"success": False, "errors": [str(e)]}

def get_all_entries():
    return get_all_local_visitors()

def get_active_visitors():
    return get_active_local_visitors()

def check_out_visitor(visitor_name, phone): 
    try:
        # Check status first from local cache
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, status FROM visitors WHERE name = ? AND phone = ? AND exit_time IS NULL", (visitor_name, phone))
        visitor = cursor.fetchone()
        
        if not visitor:
            logger.warning("No active visit found in local cache")
            return {"success": False, "errors": ["No active visit found."]}
        
        visitor_id = visitor['id']
        status = visitor['status']
        
        if status != 1:
            # Delete from Supabase and local cache
            supabase.table('visitors').delete().eq('id', visitor_id).execute()
            remove_local_visitor(visitor_id)
            msg = "Visitor entry removed (Denied/Pending)."
        else:
            # Normal exit logic
            timestamp = datetime.now().isoformat()
            payload = {
                "exit_time": timestamp,
                "updated_at": timestamp
            }
            response = supabase.table('visitors').update(payload).eq('id', visitor_id).execute()
            if response.data:
                update_local_visitor(response.data[0])
            msg = "Visitor checked out successfully."
        return {"success": True, "message": msg}
    except Exception as e:
        logger.error(f"Error checking out visitor: {e}")
        return {"success": False, "errors": [str(e)]}
    finally:
        conn.close()

def remove_all_records():
    try:
        supabase.table('visitors').delete().neq('id', -1).execute() # Hackish way to delete all if safe mode is on
        conn = get_db_connection()
        conn.execute("DELETE FROM visitors")
        conn.commit()
        conn.close()
        return "Records removed successfully."
    except Exception as e:
        return "Failed to remove the records " + str(e)

def get_latest_visitor_timestamp():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(updated_at) FROM visitors")
        t1 = cursor.fetchone()[0]
        cursor.execute("SELECT MAX(entry_time) FROM visitors")
        t2 = cursor.fetchone()[0]
        
        return max(t1, t2) if (t1 or t2) else None
    except Exception as e:
        logger.error(f"Error getting latest visitor timestamp from cache: {e}")
        return None
    finally:
        conn.close()

def get_pending_visitors(host_name):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM visitors WHERE person_to_visit = ? AND status = 0", (host_name,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting pending visitors from cache: {e}")
        return []
    finally:
        conn.close()

def get_entries_paginated(page: int = 1, per_page: int = 50) -> PaginationResult:
    result = get_paginated_local_visitors(page, per_page)
    
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
