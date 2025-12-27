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
        cur.execute('''
            SELECT id FROM visitors 
            WHERE phone = ? AND name = ? AND exit_time IS NULL
        ''', (phone, visitor_name))
        
        if cur.fetchone():
            conn.close()
            return {"success": False, "errors": ["Visitor already checked in."]}

        cur.execute('''
            INSERT INTO visitors (name, phone, person_to_visit, reason, has_vehicle, vehicle_number, entry_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (visitor_name, phone, host_name, reason, has_vehicle, vehicle_number, datetime.now().isoformat()))
        conn.commit()
    except Exception as e:
        conn.close()
        return {"success": False, "errors": [str(e)]}
    finally:
        conn.close()

    return {"success": True, "message": "Visitor registered successfully."}

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
            'exit_time': row['exit_time']
        })
    return results

def check_out_visitor(visitor_name, phone): # Changed params to simple args potentially, but sticking to logic
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE visitors 
            SET exit_time = ? 
            WHERE name = ? AND phone = ? AND exit_time IS NULL
        ''', (datetime.now().isoformat(), visitor_name, phone))
        conn.commit()
        if cur.rowcount > 0:
            return {"success": True}
        else:
            return {"success": False, "errors": ["No active visit found."]}
    finally:
        conn.close()
