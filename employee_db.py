import re
import bcrypt
import logging
from db import get_supabase_client
from cache_manager import get_local_employee, update_local_employee, remove_local_employee, get_db_connection

logger = logging.getLogger(__name__)

# Initialize Supabase client
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
            "auth_level": data["Auth_level"],
            "status": data["status"]
        }

        logger.info(f"Attempting to insert employee: {data['login_id']}")
        response = supabase.table('employee').insert(payload).execute()
        
        if response.data:
            logger.info(f"Employee created successfully: {data['login_id']}")
            # Update local cache
            update_local_employee(response.data[0])
            return True
        else:
            logger.error(f"Insert returned no data. Response: {response}")
            return False
    except Exception as e:
        logger.exception(f"Error inserting employee: {e}")
        return False

def get_employee_by_name(data):
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT * FROM employee WHERE name = ?', (data["name"],))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return "Employee not found"
    except Exception as e:
        logger.error(f"Error getting employee by name from cache: {e}")
        return None
    finally:
        conn.close()

def get_employee_phone(name):
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT phone FROM employee WHERE name = ?', (name,))
        row = cursor.fetchone()
        if row:
            return row['phone']
        return None
    except Exception as e:
        logger.error(f"Error getting employee phone from cache: {e}")
        return False
    finally:
        conn.close()

def check_credentials(login_id, password):
    """
    Check employee credentials with password verification.
    Uses local cache for performance.
    """
    try:
        # Fetch employee from LOCAL CACHE
        employee = get_local_employee(login_id)
        
        if employee:
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
        payload = {'status': status}
        
        # If setting to Offline (0), also clear connection info
        if status == 0:
            payload['ip_address'] = None
            payload['connection_mode'] = None
            
        response = supabase.table('employee').update(payload).eq('login_id', login_id).execute()
        
        if response.data:
            print(f"Updated status to {status} for {login_id}")
            update_local_employee(response.data[0])
            return True
        else:
            print(f"Warning: update_employee_status - No employee found with login_id: {login_id}")
            return True
    except Exception as e:
        logger.error(f"Error updating employee status: {e}")
        return False

def get_employee_status(login_id):
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT status FROM employee WHERE login_id = ?', (login_id,))
        row = cursor.fetchone()
        if row:
            return row['status']
        return None
    except Exception as e:
        logger.error(f"Error getting employee status from cache: {e}")
        return None
    finally:
        conn.close()

def get_all_employees():
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT name, login_id FROM employee')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all employees from cache: {e}")
        return []
    finally:
        conn.close()

def get_all_employees_full(search=None, role=None, status=None):
    conn = get_db_connection()
    try:
        query = 'SELECT name, login_id, phone, Auth_level, status FROM employee WHERE 1=1'
        params = []
        
        if search:
            query += ' AND (name LIKE ? OR login_id LIKE ? OR phone LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if role:
            query += ' AND Auth_level = ?'
            params.append(int(role))
        
        if status is not None and status != '':
            query += ' AND status = ?'
            params.append(int(status))
            
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all employees full from cache: {e}")
        return []
    finally:
        conn.close()

def reset_all_employee_statuses():
    """Resets the status of all employees to 0 (Offline)."""
    
    try:
        response = supabase.table('employee').update({'status': 0}).neq('status', 0).execute()
        print("All employee statuses have been reset to 0.")
        # Sync the changes to the local cache
        from cache_manager import sync_data_from_supabase
        sync_data_from_supabase(force=True)
        return True
    except Exception as e:
        logger.error(f"Error resetting employee statuses: {e}")
        return False

def delete_employee(login_id):
    """Deletes an employee and triggers a backup."""
    
    try:
        response = supabase.table('employee').delete().eq('login_id', login_id).execute()
        if response.data:
            print(f"Employee {login_id} deleted successfully.")
            logger.info(f"Employee deleted: {login_id}")
            # Update local cache
            remove_local_employee(login_id)
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting employee {login_id}: {e}")
        return False

def update_employee_connection(login_id, ip_address, mode):
    """
    Updates the employee's connection info (IP and Mode) upon login.
    """
    try:
        payload = {
            'ip_address': ip_address,
            'connection_mode': mode,
            'status': 1 # Ensure they are marked Online
        }
        
        response = supabase.table('employee').update(payload).eq('login_id', login_id).execute()
        
        if response.data:
            logger.info(f"Updated connection info for {login_id}: {mode} ({ip_address})")
            # Update local cache
            update_local_employee(response.data[0])
            return True
        else:
            logger.warning(f"Failed to update connection info for {login_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating employee connection info: {e}")
        return False