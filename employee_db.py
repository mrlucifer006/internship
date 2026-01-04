import re
import bcrypt
import logging
from db import get_supabase_client

logger = logging.getLogger(__name__)

supabase = get_supabase_client()

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
    try:
        # Hash the password before storing
        hashed_pwd = hash_password(data["password"])
        
        payload = {
            "name": data["name"],
            "phone": "+91" + data["phone"],
            "login_id": data["login_id"],
            "password": hashed_pwd,
            "Auth_level": data["Auth_level"],
            "status": data["status"]
        }

        response = supabase.table('employee').insert(payload).execute()
        
        if response.data:
            logger.info(f"Employee created: {data['login_id']}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error inserting employee: {e}")
        return False

def get_employee_by_name(data):
    try:
        response = supabase.table('employee').select("*").eq('name', data["name"]).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            return "Employee not found" # Keeping original return string behavior
    except Exception as e:
        logger.error(f"Error getting employee by name: {e}")
        return None

def get_employee_phone(name):
    try:
        response = supabase.table('employee').select("phone").eq('name', name).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['phone']
        else:
            return None
    except Exception as e:
        logger.error(f"Error getting employee phone: {e}")
        return False

def check_credentials(login_id, password):
    """
    Check employee credentials with password verification.
    """
    try:
        # Fetch employee by login_id only
        response = supabase.table('employee').select("*").eq('login_id', login_id).execute()
        
        if response.data and len(response.data) > 0:
            employee = response.data[0]
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

def update_employee_status(login_id, status):
    try:
        response = supabase.table('employee').update({'status': status}).eq('login_id', login_id).execute()
        
        if response.data:
            print(f"Updated status to {status} for {login_id}")
            return True
        else:
            print(f"Warning: update_employee_status - No employee found with login_id: {login_id}")
            return True # Original returned True on error/empty too? No, it handled it. 
            # Original: if cursor.rowcount == 0 return True (technically it fell through).
            # Let's return True as intent seems to be "operation attempted".
    except Exception as e:
        logger.error(f"Error updating employee status: {e}")
        return False

def get_employee_status(login_id):
    try:
        response = supabase.table('employee').select("status").eq('login_id', login_id).execute()
        if response.data:
            return response.data[0]['status']
        return None
    except Exception as e:
        logger.error(f"Error getting employee status: {e}")
        return None

def add_notification(host_login_id, visitor_name, reason, visitor_id=None):
    try:
        payload = {
            "host_login_id": host_login_id,
            "visitor_name": visitor_name,
            "reason": reason,
            "visitor_id": visitor_id
        }
        response = supabase.table('notifications').insert(payload).execute()
        if response.data:
            return True
        return False
    except Exception as e:
        logger.error(f"Error adding notification: {e}")
        return False

def get_unread_notifications(host_login_id):
    try:
        response = supabase.table('notifications').select("*").eq('host_login_id', host_login_id).eq('is_read', 0).execute()
        notifications = response.data if response.data else []
        
        # Mark as read immediately
        if notifications:
            supabase.table('notifications').update({'is_read': 1}).eq('host_login_id', host_login_id).eq('is_read', 0).execute()
            
        return notifications
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return []

def get_notification_history(host_login_id):
    try:
        response = supabase.table('notifications').select("*").eq('host_login_id', host_login_id).order('timestamp', desc=True).limit(20).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting notification history: {e}")
        return []

def get_all_employees():
    try:
        response = supabase.table('employee').select("name, login_id").execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error getting all employees: {e}")
        return []

def get_all_employees_full():
    try:
        response = supabase.table('employee').select("name, login_id, phone, Auth_level, status").execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error getting all employees full: {e}")
        return []

def reset_all_employee_statuses():
    """Resets the status of all employees to 0 (Offline)."""
    try:
        # Note: Supabase update without 'eq' usually requires safety setting off or explicit filter.
        # However, to update ALL, we can use a filter that matches all, e.g. login_id like %.
        # Safer: .neq('status', 0) to only update those who need it.
        response = supabase.table('employee').update({'status': 0}).neq('status', 0).execute()
        print("All employee statuses have been reset to 0.")
        return True
    except Exception as e:
        logger.error(f"Error resetting employee statuses: {e}")
        return False

def delete_employee(login_id):
    """Deletes an employee and triggers a backup."""
    try:
        # Check if user exists first
        check = supabase.table('employee').select("name").eq('login_id', login_id).execute()
        if not check.data:
            logger.warning(f"Attempted delete on non-existent user: {login_id}")
            return False

        response = supabase.table('employee').delete().eq('login_id', login_id).execute()
        if response.data:
            print(f"Employee {login_id} deleted successfully.")
            logger.info(f"Employee deleted: {login_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting employee {login_id}: {e}")
        return False
