from db import get_db_connection
from datetime import datetime
import sqlite3

def save_visitor(data):
    """
    Validates and saves visitor data.
    Expected keys: name, Number (phone), V_name (visitor name), reason, vehicle, vehicle_number (optional)
    """
    errors = []
    
    # Keys from app.py: name (host), Number (visitor phone), V_name (visitor name), reason, vehicle, vehicle_number
    # DB Scheme: name (visitor name?), phone, person_to_visit, reason, has_vehicle, vehicle_number, entry_time
    
    # Mapping based on app.py usage:
    # app.py: name -> Host Name
    # app.py: V_name -> Visitor Name
    # db.py scheme: name -> Visitor Name (implied by typical logic, but let's check init_db)
    # db.py: name, phone, person_to_visit...
    
    # Let's map: 
    # data['V_name'] -> DB 'name' (Visitor Name)
    # data['Number'] -> DB 'phone'
    # data['name'] -> DB 'person_to_visit' (Host)
    
    host_name = data.get("name")
    phone = data.get("Number")
    visitor_name = data.get("V_name")
    reason = data.get("reason")
    vehicle = data.get("vehicle") # "on" if checked, None otherwise, or "true"/"false" strings? 
    # app.py sends: vehicle = flask.request.form.get('vehicle') -> likely 'on' or None if checkbox.
    vehicle_number = data.get("vehicle_number")

    if not host_name: errors.append("Host name is required.")
    if not phone: errors.append("Phone number is required.")
    if not visitor_name: errors.append("Visitor name is required.")
    if not reason: errors.append("Reason is required.")

    has_vehicle = 1 if vehicle else 0
    if has_vehicle and not vehicle_number:
         # It's possible the user ticked it but didn't fill number. Logic says required.
         # But app.py logic was: if vehicle: vehicle_number = ...
         pass 

    if errors:
        return {"success": False, "errors": errors}

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Simple duplicate check: entry matching phone & visitor name that hasn't exited 
        # But allow re-entry if the previous status was 'Denied'
        cur.execute('''
            SELECT id FROM visitors 
            WHERE phone = ? AND name = ? AND exit_time IS NULL AND approval_status != 'Denied'
        ''', (phone, visitor_name))
        
        if cur.fetchone():
            conn.close()
            return {"success": False, "errors": ["Visitor already checked in."]}

        # Default status is 'Approved' unless specified
        approval_status = data.get("approval_status", "Approved")

        cur.execute('''
            INSERT INTO visitors (name, phone, person_to_visit, reason, has_vehicle, vehicle_number, entry_time, approval_status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (visitor_name, 
        phone, host_name, reason, has_vehicle, vehicle_number, datetime.now().isoformat(), approval_status, datetime.now().isoformat()))
        conn.commit()
        visitor_id = cur.lastrowid
    except Exception as e:
        conn.close()
        return {"success": False, "errors": [str(e)]}
    finally:
        conn.close()

    return {"success": True, "message": "Visitor registered successfully.", "visitor_id": visitor_id}

def get_all_entries():
    conn = get_db_connection()
    visitors = conn.execute('SELECT * FROM visitors').fetchall()
    conn.close()
    
    # Convert to list of dicts matching app expectation
    # App expects: V_name, name (host), reason, Number, vehicle (bool/str), vehicle_number
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
            'approval_status': row['approval_status'] if 'approval_status' in row.keys() else 'Approved',
            'denial_reason': row['denial_reason'] if 'denial_reason' in row.keys() else None
        })
    return results

def get_active_visitors():
    conn = get_db_connection()
    visitors = conn.execute('SELECT * FROM visitors WHERE exit_time IS NULL').fetchall()
    conn.close()
    
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
            'approval_status': row['approval_status'] if 'approval_status' in row.keys() else 'Approved',
            'denial_reason': row['denial_reason'] if 'denial_reason' in row.keys() else None,
            'id': row['id']
        })
    return results

def check_out_visitor(visitor_name, phone): 
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Check status first
        print(f"DEBUG: checking DB for name='{visitor_name}', phone='{phone}'")
        cur.execute("SELECT approval_status FROM visitors WHERE name = ? AND phone = ? AND exit_time IS NULL", (visitor_name, phone))
        row = cur.fetchone()
        
        if not row:
            print("DEBUG: No active visit found in DB")
            return {"success": False, "errors": ["No active visit found."]}
            
        status = row['approval_status']
        
        if status != 'Approved':
            # Notification/Alert: "Don't add to database"
            # Delete the record entirely to remove trace
            cur.execute("DELETE FROM visitors WHERE name = ? AND phone = ? AND exit_time IS NULL", (visitor_name, phone))
            msg = "Visitor entry removed (Denied/Pending)."
        else:
            # Normal exit logic
            timestamp = datetime.now().isoformat()
            cur.execute('''
                UPDATE visitors 
                SET exit_time = ?, updated_at = ?
                WHERE name = ? AND phone = ? AND exit_time IS NULL
            ''', (timestamp, timestamp, visitor_name, phone))
            msg = "Visitor checked out successfully."
            
        conn.commit()
        return {"success": True, "message": msg}
    finally:
        conn.close()

def remove_all_records():
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM visitors")
        conn.commit()
    except Exception as e:
        conn.close()
        return "Failed to remove the records " + str(e)
    finally:
        conn.close()
    return "Records removed successfully."

def get_latest_visitor_timestamp():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Check MAX of updated_at OR entry_time (fallback)
        cur.execute("SELECT MAX(COALESCE(updated_at, entry_time)) as last_updated FROM visitors")
        row = cur.fetchone()
        if row and row['last_updated']:
            return row['last_updated']
        return None
    except Exception:
        return None
    finally:
        conn.close()

