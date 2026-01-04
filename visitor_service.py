from db import get_supabase_client
from pagination import PaginationResult
from datetime import datetime
import logging
import math

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
        # Simple duplicate check: entry matching phone & visitor name that hasn't exited 
        # But allow re-entry if the previous status was 'Denied'
        
        # Check active visits
        check_query = supabase.table('visitors').select("id").eq('phone', phone).eq('name', visitor_name).is_('exit_time', 'null').neq('approval_status', 'Denied').execute()
        
        if check_query.data:
            return {"success": False, "errors": ["Visitor already checked in."]}

        # Default status is 'Approved' unless specified
        approval_status = data.get("approval_status", "Approved")
        
        payload = {
            "name": visitor_name,
            "phone": phone,
            "person_to_visit": host_name,
            "reason": reason,
            "has_vehicle": has_vehicle,
            "vehicle_number": vehicle_number,
            "entry_time": datetime.now().isoformat(),
            "approval_status": approval_status, 
            "updated_at": datetime.now().isoformat()
        }

        response = supabase.table('visitors').insert(payload).execute()
        
        if response.data:
            visitor_id = response.data[0]['id']
            return {"success": True, "message": "Visitor registered successfully.", "visitor_id": visitor_id}
        else:
             return {"success": False, "errors": ["Database insert failed."]}

    except Exception as e:
        logger.error(f"Error saving visitor: {e}")
        return {"success": False, "errors": [str(e)]}

def get_all_entries():
    try:
        response = supabase.table('visitors').select("*").execute()
        visitors = response.data if response.data else []
        
        results = []
        for row in visitors:
            results.append({
                'V_name': row['name'],
                'Number': row['phone'],
                'name': row['person_to_visit'],
                'reason': row['reason'],
                'vehicle': row['has_vehicle'],
                'vehicle_number': row['vehicle_number'],
                'entry_time': row['entry_time'],
                'exit_time': row['exit_time'],
                'approval_status': row.get('approval_status', 'Approved'),
                'denial_reason': row.get('denial_reason')
            })
        return results
    except Exception as e:
        logger.error(f"Error getting all entries: {e}")
        return []

def get_active_visitors():
    try:
        response = supabase.table('visitors').select("*").is_('exit_time', 'null').execute()
        visitors = response.data if response.data else []
        
        results = []
        for row in visitors:
            results.append({
                'V_name': row['name'],
                'Number': row['phone'],
                'name': row['person_to_visit'],
                'reason': row['reason'],
                'vehicle': row['has_vehicle'],
                'vehicle_number': row['vehicle_number'],
                'entry_time': row['entry_time'],
                'approval_status': row.get('approval_status', 'Approved'),
                'denial_reason': row.get('denial_reason'),
                'id': row['id']
            })
        return results
    except Exception as e:
        logger.error(f"Error getting active visitors: {e}")
        return []

def check_out_visitor(visitor_name, phone): 
    try:
        # Check status first
        response = supabase.table('visitors').select("approval_status").eq('name', visitor_name).eq('phone', phone).is_('exit_time', 'null').execute()
        
        if not response.data:
            logger.warning("No active visit found in DB")
            return {"success": False, "errors": ["No active visit found."]}
        
        status = response.data[0]['approval_status']
        
        if status != 'Approved':
            # Notification/Alert: "Don't add to database"
            # Delete the record entirely to remove trace
            supabase.table('visitors').delete().eq('name', visitor_name).eq('phone', phone).is_('exit_time', 'null').execute()
            msg = "Visitor entry removed (Denied/Pending)."
        else:
            # Normal exit logic
            timestamp = datetime.now().isoformat()
            payload = {
                "exit_time": timestamp,
                "updated_at": timestamp
            }
            supabase.table('visitors').update(payload).eq('name', visitor_name).eq('phone', phone).is_('exit_time', 'null').execute()
            msg = "Visitor checked out successfully."
        return {"success": True, "message": msg}
    except Exception as e:
        logger.error(f"Error checking out visitor: {e}")
        return {"success": False, "errors": [str(e)]}

def remove_all_records():
    try:
        # Deleting all rows requires a filter or explicit 'neq'. 
        supabase.table('visitors').delete().neq('id', -1).execute() # Hackish way to delete all if safe mode is on
        return "Records removed successfully."
    except Exception as e:
        return "Failed to remove the records " + str(e)

def get_latest_visitor_timestamp():
    try:
        # Check MAX of updated_at OR entry_time.
        # Supabase doesn't support complex COALESCE in select easily without RPC.
        # We'll fetch latest updated_at and latest entry_time and compare.
        # OR just order by updated_at desc limit 1.
        
        res_updated = supabase.table('visitors').select("updated_at").order('updated_at', desc=True).limit(1).execute()
        res_entry = supabase.table('visitors').select("entry_time").order('entry_time', desc=True).limit(1).execute()
        
        t1 = res_updated.data[0]['updated_at'] if res_updated.data and res_updated.data[0]['updated_at'] else ""
        t2 = res_entry.data[0]['entry_time'] if res_entry.data and res_entry.data[0]['entry_time'] else ""
        
        return max(t1, t2) if (t1 or t2) else None
    except Exception:
        return None

def get_entries_paginated(page: int = 1, per_page: int = 50) -> PaginationResult:
    """
    Get visitor entries with pagination.
    """
    try:
        # Start building the query
        query = supabase.table('visitors').select("*", count='exact')
        
        # Order by ID descending (newest first)
        query = query.order('id', desc=True)
            
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page - 1 
        
        response = query.range(start, end).execute()
        
        visitors = response.data if response.data else []
        total = response.count if response.count is not None else 0
        
        mapped_data = []
        for row in visitors:
            mapped_data.append({
                'V_name': row['name'],
                'Number': row['phone'],
                'name': row['person_to_visit'],
                'reason': row['reason'],
                'vehicle': row['has_vehicle'],
                'vehicle_number': row['vehicle_number'],
                'entry_time': row['entry_time'],
                'exit_time': row['exit_time'],
                'approval_status': row.get('approval_status', 'Approved'),
                'denial_reason': row.get('denial_reason'),
                'id': row['id']
            })
            
        total_pages = math.ceil(total / per_page) if total else 1
        has_next = page < total_pages
        has_prev = page > 1
        
        return PaginationResult(
            data=mapped_data,
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        logger.error(f"Error getting paginated entries: {e}")
        return PaginationResult(
            data=[],
            page=1,
            per_page=per_page,
            total=0,
            total_pages=1,
            has_next=False,
            has_prev=False
        )
