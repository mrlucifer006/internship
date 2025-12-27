from .db import get_db_connection
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

def insert(data):
    """
    Saves visitor data to the SQLite database (Stack Push).
    """
    conn = get_db_connection()
    try:
        # 1 if has_vehicle is True/truthy, else 0
        has_vehicle_int = 1 if data.get("has_vehicle") else 0
        
        query = """
            INSERT INTO visitors (ticket_number, name, phone, person_to_visit, reason, has_vehicle, vehicle_number, entry_time, exit_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            data.get("ticket_number"),
            data["name"],
            data["phone"],
            data["person_to_visit"],
            data["reason"],
            has_vehicle_int,
            data.get("vehicle_number"),
            datetime.now(IST).isoformat(),
            None
        )
        
        cursor = conn.execute(query, values)
        conn.commit()
        return {"success": True, "message": "Visitor registered successfully.", "id": str(cursor.lastrowid)}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def get_visitors(limit=1):
    """
    Retrieves visitor records ordered by entry_time descending (LIFO).
    Args:
        limit (int): Number of records to retrieve. Default is 1 (Stack Peek).
    """
    conn = get_db_connection()
    try:
        query = "SELECT * FROM visitors ORDER BY entry_time DESC LIMIT ?"
        rows = conn.execute(query, (limit,)).fetchall()
        return {"success": True, "data": [dict(row) for row in rows]}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def get_visitor_by_ticket(ticket_number):
    """
    Retrieves a visitor record by ticket number.
    """
    conn = get_db_connection()
    try:
        query = "SELECT * FROM visitors WHERE ticket_number = ?"
        row = conn.execute(query, (ticket_number,)).fetchone()
        
        if row:
            return {"success": True, "data": dict(row)}
        return {"success": False, "error": "Visitor not found."}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def update_exit_time(name, phone):
    """
    Updates the exit time for the most recent active visitor record (Stack Pop).
    Ensures consistency by closing the correct session.
    """
    conn = get_db_connection()
    try:
        # Find the latest active record ID for this user (Stack Top)
        query_find = """
            SELECT id FROM visitors 
            WHERE name = ? AND phone = ? AND exit_time IS NULL
            ORDER BY entry_time DESC
            LIMIT 1
        """
        row = conn.execute(query_find, (name, phone)).fetchone()
        
        if not row:
             return {"success": False, "error": "No active check-in found for this visitor."}

        # Update that specific record
        visitor_id = row['id']
        query_update = "UPDATE visitors SET exit_time = ? WHERE id = ?"
        conn.execute(query_update, (datetime.now(IST).isoformat(), visitor_id))
        conn.commit()
        
        return {"success": True, "message": "Visitor checked out successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

