import sqlite3
import re
import bcrypt
import logging
from db import get_db_connection, trigger_backup

logger = logging.getLogger(__name__)

# NOTE: DB_NAME is now managed in db.py

def hash_password(password):
    """
    Hash a password using bcrypt.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password, hashed_password):
    """
    Verify a password against a hash.
    Supports both bcrypt hashed passwords and plain text for backward compatibility.
    """
    if not hashed_password:
        return False
    
    # Check if it's a bcrypt hash (starts with $2b$)
    if hashed_password.startswith('$2b$'):
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    else:
        # Backward compatibility: plain text comparison
        logger.warning("Plain text password detected. Please migrate to hashed passwords.")
        return plain_password == hashed_password


def insert_employee(data):
    """
    Insert a new employee with hashed password.
    """
    conn = get_db_connection()
    try:
        # Hash the password before storing
        hashed_pwd = hash_password(data["password"])
        
        with conn:
            conn.execute(
                "INSERT INTO employee (name, phone, login_id, password, Auth_level, status) VALUES (?, ?, ?, ?, ?, ?)",
                (data["name"], "+91"+data["phone"], data["login_id"], hashed_pwd, data["Auth_level"], data["status"])
            )
            logger.info(f"Employee created: {data['login_id']}")
            trigger_backup() # BACKUP TRIGGER
            return True
    except Exception as e:
        logger.error(f"Error inserting employee: {e}")
        return False
    finally:
        conn.close()

def get_employee_by_name(data):
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT * FROM employee WHERE name = ?", (data["name"],))
        row = cursor.fetchone()
        if row:
            return dict(row)
        else:
            return "Employee not found"
    except Exception as e:
        logger.error(f"Error getting employee by name: {e}")
        return None
    finally:
        conn.close()

def get_employee_phone(name):
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute("SELECT phone FROM employee WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return row['phone']
            else:
                return None
    except Exception as e:
        logger.error(f"Error getting employee phone: {e}")
        return False
    finally:
        conn.close()

def check_credentials(login_id, password):
    """
    Check employee credentials with password verification.
    """
    conn = get_db_connection()
    try:
        # Fetch employee by login_id only
        cursor = conn.execute("SELECT * FROM employee WHERE login_id = ?", (login_id,))
        row = cursor.fetchone()
        
        if row:
            employee = dict(row)
            # Verify password using bcrypt or plain text
            if verify_password(password, employee['password']):
                logger.info(f"Successful login: {login_id}")
                return employee
            else:
                logger.warning(f"Failed login attempt for: {login_id}")
                return None
        else:
            logger.warning(f"Login attempt for non-existent user: {login_id}")
            return None
    except Exception as e:
        logger.error(f"Login Check Error: {e}")
        return None
    finally:
        conn.close()            

def update_employee_status(login_id, status):
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute("UPDATE employee SET status = ? WHERE login_id = ?", (status, login_id))
            if cursor.rowcount == 0:
                print(f"Warning: update_employee_status - No employee found with login_id: {login_id}")
            else:
                print(f"Updated status to {status} for {login_id}")
                trigger_backup() # BACKUP TRIGGER
        return True
    except Exception as e:
        logger.error(f"Error updating employee status: {e}")
        return False
    finally:
        conn.close()

def get_employee_status(login_id):
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT status FROM employee WHERE login_id = ?", (login_id,))
        row = cursor.fetchone()
        if row:
            return row['status']
        return None
    except Exception as e:
        logger.error(f"Error getting employee status: {e}")
        return None
    finally:
        conn.close()

def add_notification(host_login_id, visitor_name, reason, visitor_id=None):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("INSERT INTO notifications (host_login_id, visitor_name, reason, visitor_id) VALUES (?, ?, ?, ?)", (host_login_id, visitor_name, reason, visitor_id))
        trigger_backup() # BACKUP TRIGGER
        return True
    except Exception as e:
        logger.error(f"Error adding notification: {e}")
        return False
    finally:
        conn.close()

def get_unread_notifications(host_login_id):
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute("SELECT * FROM notifications WHERE host_login_id = ? AND is_read = 0", (host_login_id,))
            rows = cursor.fetchall()
            notifications = [dict(row) for row in rows]
            
            # Mark as read immediately
            if notifications:
                conn.execute("UPDATE notifications SET is_read = 1 WHERE host_login_id = ? AND is_read = 0", (host_login_id,))
                trigger_backup() # BACKUP TRIGGER
            
            return notifications
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return []
    finally:
        conn.close()

def get_notification_history(host_login_id):
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute("SELECT * FROM notifications WHERE host_login_id = ? ORDER BY timestamp DESC LIMIT 20", (host_login_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error getting notification history: {e}")
        return []
    finally:
        conn.close()

def get_all_employees():
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT name, login_id FROM employee")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all employees: {e}")
        return []
    finally:
        conn.close()

def get_all_employees_full():
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT name, login_id, phone, Auth_level, status FROM employee")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all employees full: {e}")
        return []
    finally:
        conn.close()

def reset_all_employee_statuses():
    """Resets the status of all employees to 0 (Offline)."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("UPDATE employee SET status = 0")
            print("All employee statuses have been reset to 0.")
            trigger_backup() # BACKUP TRIGGER
        return True
    except Exception as e:
        logger.error(f"Error resetting employee statuses: {e}")
        return False
    finally:
        conn.close()

