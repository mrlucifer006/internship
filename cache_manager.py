import sqlite3
import logging
from db import get_supabase_client

logger = logging.getLogger(__name__)

DB_FILE = 'local_cache.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_cache():
    """Initialize the local cache database."""
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS employee (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                login_id TEXT UNIQUE,
                phone TEXT,
                password TEXT,
                Auth_level INTEGER,
                status INTEGER,
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS visitors (
                id INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT,
                person_to_visit TEXT,
                reason TEXT,
                has_vehicle INTEGER,
                vehicle_number TEXT,
                entry_time TEXT,
                exit_time TEXT,
                status INTEGER,
                denial_reason TEXT,
                updated_at TEXT,
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicle (
                id INTEGER PRIMARY KEY,
                driver_name TEXT,
                veh_reg_no TEXT UNIQUE,
                vehicle_img TEXT,
                destination TEXT,
                "time" TEXT,
                driver_phone TEXT,
                origin TEXT,
                purchase_no TEXT,
                entry_type TEXT,
                created_at TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        logger.error(f"Error initializing local cache: {e}")
    finally:
        conn.close()

def sync_data_from_supabase(force=False):
    """Fetch all data from Supabase and populate the local cache."""
    conn = get_db_connection()
    try:
        if not force:
            # Check if the cache is already populated
            cursor = conn.execute('SELECT COUNT(id) FROM employee')
            count = cursor.fetchone()[0]
            if count > 0:
                logger.info(f"Cache already has {count} records. Skipping sync.")
                print(f"Cache already has {count} records. Skipping sync.")
                return True

        # If cache is empty or force is True, proceed with sync
        supabase = get_supabase_client()
        logger.info("Syncing data from Supabase...")

        # Sync employees
        employees = supabase.table('employee').select("*").execute().data
        if employees:
            conn.execute('DELETE FROM employee')
            for emp in employees:
                conn.execute('''
                    INSERT INTO employee (id, name, login_id, phone, password, Auth_level, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    emp.get('id'),
                    emp.get('name'),
                    emp.get('login_id'),
                    emp.get('phone'),
                    emp.get('password'),
                    emp.get('Auth_level'),
                    emp.get('status', 0),
                    emp.get('created_at')
                ))

        # Sync visitors
        visitors = supabase.table('visitors').select('*').execute().data
        if visitors:
            conn.execute('DELETE FROM visitors')
            for v in visitors:
                conn.execute('''
                    INSERT INTO visitors (id, name, phone, person_to_visit, reason, has_vehicle, vehicle_number, entry_time, exit_time, status, denial_reason, updated_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    v.get('id'),
                    v.get('name'),
                    v.get('phone'),
                    v.get('person_to_visit'),
                    v.get('reason'),
                    v.get('has_vehicle'),
                    v.get('vehicle_number'),
                    v.get('entry_time'),
                    v.get('exit_time'),
                    v.get('status'),
                    v.get('denial_reason'),
                    v.get('updated_at'),
                    v.get('created_at')
                ))

        # Sync vehicles
        vehicles = supabase.table('vehicle').select('*').execute().data
        if vehicles:
            conn.execute('DELETE FROM vehicle')
            for v in vehicles:
                conn.execute('''
                    INSERT INTO vehicle (id, driver_name, veh_reg_no, vehicle_img, destination, "time", driver_phone, origin, purchase_no, entry_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    v.get('id'),
                    v.get('driver_name'),
                    v.get('veh_reg_no'),
                    v.get('vehicle_img'),
                    v.get('destination'),
                    v.get('time'),
                    v.get('driver_phone'),
                    v.get('origin'),
                    v.get('purchase_no'),
                    v.get('entry_type'),
                    v.get('created_at')
                ))
        
        conn.commit()
        logger.info("Cache synced with Supabase.")
        print("Cache synced with Supabase.")
        return True
    except Exception as e:
        logger.error(f"Error syncing data from Supabase: {e}")
        print(f"Error syncing data from Supabase: {e}")
        return False
    finally:
        conn.close()

def get_local_employee(login_id):
    """Retrieve an employee from the local cache by login_id."""
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT * FROM employee WHERE login_id = ?', (login_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        logger.error(f"Error getting local employee: {e}")
        return None
    finally:
        conn.close()

def update_local_employee(data):
    """Update or Insert an employee in the local cache."""
    conn = get_db_connection()
    try:
        # Check if exists
        exists = conn.execute('SELECT 1 FROM employee WHERE id = ?', (data['id'],)).fetchone()
        
        if exists:
             conn.execute('''
                UPDATE employee 
                SET name=?, phone=?, password=?, Auth_level=?, status=?, login_id=?
                WHERE id=?
            ''', (
                data.get('name'),
                data.get('phone'),
                data.get('password'),
                data.get('Auth_level'),
                data.get('status'),
                data.get('login_id'),
                data.get('id')
            ))
        else:
            conn.execute('''
                INSERT INTO employee (id, name, login_id, phone, password, Auth_level, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('id'),
                data.get('name'),
                data.get('login_id'),
                data.get('phone'),
                data.get('password'),
                data.get('Auth_level'),
                data.get('status')
            ))
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating local employee cache: {e}")
    finally:
        conn.close()

def remove_local_employee(login_id):
    """Remove an employee from the local cache."""
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM employee WHERE login_id = ?', (login_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Error removing local employee: {e}")
    finally:
        conn.close()

def get_local_visitor(visitor_id):
    """Retrieve a visitor from the local cache by visitor_id."""
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT * FROM visitors WHERE id = ?', (visitor_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        logger.error(f"Error getting local visitor: {e}")
        return None
    finally:
        conn.close()

def update_local_visitor(data):
    """Update or Insert a visitor in the local cache."""
    conn = get_db_connection()
    try:
        # Check if exists
        exists = conn.execute('SELECT 1 FROM visitors WHERE id = ?', (data['id'],)).fetchone()
        
        if exists:
                conn.execute('''
                    UPDATE visitors
                    SET name=?, phone=?, person_to_visit=?, reason=?, has_vehicle=?, vehicle_number=?, entry_time=?, exit_time=?, status=?, denial_reason=?, updated_at=?, created_at=?
                    WHERE id=?
                ''', (
                    data.get('name'),
                    data.get('phone'),
                    data.get('person_to_visit'),
                    data.get('reason'),
                    data.get('has_vehicle'),
                    data.get('vehicle_number'),
                    data.get('entry_time'),
                    data.get('exit_time'),
                    data.get('status'),
                    data.get('denial_reason'),
                    data.get('updated_at'),
                    data.get('created_at'),
                    data.get('id')
                ))
        else:
            conn.execute('''
                INSERT INTO visitors (id, name, phone, person_to_visit, reason, has_vehicle, vehicle_number, entry_time, exit_time, status, denial_reason, updated_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('id'),
                data.get('name'),
                data.get('phone'),
                data.get('person_to_visit'),
                data.get('reason'),
                data.get('has_vehicle'),
                data.get('vehicle_number'),
                data.get('entry_time'),
                data.get('exit_time'),
                data.get('status'),
                data.get('denial_reason'),
                data.get('updated_at'),
                data.get('created_at')
            ))
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating local visitor cache: {e}")
    finally:
        conn.close()

def remove_local_visitor(visitor_id):
    """Remove a visitor from the local cache."""
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM visitors WHERE id = ?', (visitor_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Error removing local visitor: {e}")
    finally:
        conn.close()

def get_local_vehicle(vehicle_id):
    """Retrieve a vehicle from the local cache by vehicle_id."""
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT * FROM vehicle WHERE id = ?', (vehicle_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        logger.error(f"Error getting local vehicle: {e}")
        return None
    finally:
        conn.close()

def update_local_vehicle(data):
    """Update or Insert a vehicle in the local cache."""
    conn = get_db_connection()
    try:
        # Check if exists
        exists = conn.execute('SELECT 1 FROM vehicle WHERE id = ?', (data['id'],)).fetchone()
        
        if exists:
            conn.execute('''
                UPDATE vehicle
                SET driver_name=?, veh_reg_no=?, vehicle_img=?, destination=?, "time"=?, driver_phone=?, origin=?, purchase_no=?, entry_type=?, created_at=?
                WHERE id=?
            ''', (
                data.get('driver_name'),
                data.get('veh_reg_no'),
                data.get('vehicle_img'),
                data.get('destination'),
                data.get('time'),
                data.get('driver_phone'),
                data.get('origin'),
                data.get('purchase_no'),
                data.get('entry_type'),
                data.get('created_at'),
                data.get('id')
            ))
        else:
            conn.execute('''
                INSERT INTO vehicle (id, driver_name, veh_reg_no, vehicle_img, destination, "time", driver_phone, origin, purchase_no, entry_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('id'),
                data.get('driver_name'),
                data.get('veh_reg_no'),
                data.get('vehicle_img'),
                data.get('destination'),
                data.get('time'),
                data.get('driver_phone'),
                data.get('origin'),
                data.get('purchase_no'),
                data.get('entry_type'),
                data.get('created_at')
            ))
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating local vehicle cache: {e}")
    finally:
        conn.close()

def remove_local_vehicle(vehicle_id):
    """Remove a vehicle from the local cache."""
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM vehicle WHERE id = ?', (vehicle_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Error removing local vehicle: {e}")
    finally:
        conn.close()

def get_all_local_visitors():
    """Retrieve all visitors from the local cache."""
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT * FROM visitors')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all local visitors: {e}")
        return []
    finally:
        conn.close()

def get_active_local_visitors():
    """Retrieve all active visitors from the local cache."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT * FROM visitors WHERE exit_time IS NULL")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting active local visitors: {e}")
        return []
    finally:
        conn.close()

def get_paginated_local_visitors(page=1, per_page=10):
    """Retrieve paginated visitors from the local cache."""
    conn = get_db_connection()
    try:
        offset = (page - 1) * per_page
        cursor = conn.execute('SELECT * FROM visitors ORDER BY id DESC LIMIT ? OFFSET ?', (per_page, offset))
        rows = cursor.fetchall()
        
        total_cursor = conn.execute('SELECT COUNT(id) FROM visitors')
        total = total_cursor.fetchone()[0]
        
        return {
            "data": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "per_page": per_page
        }
    except Exception as e:
        logger.error(f"Error getting paginated local visitors: {e}")
        return {"data": [], "total": 0, "page": page, "per_page": per_page}
    finally:
        conn.close()

def get_all_local_vehicles():
    """Retrieve all vehicles from the local cache."""
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT * FROM vehicle')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all local vehicles: {e}")
        return []
    finally:
        conn.close()

def get_paginated_local_vehicles(page=1, per_page=10, search=None):
    """Retrieve paginated vehicles from the local cache."""
    conn = get_db_connection()
    try:
        offset = (page - 1) * per_page
        
        query = 'SELECT * FROM vehicle'
        params = []
        
        if search:
            query += ' WHERE veh_reg_no LIKE ?'
            params.append(f'%{search}%')
            
        query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        total_cursor = conn.execute('SELECT COUNT(id) FROM vehicle')
        total = total_cursor.fetchone()[0]
        
        return {
            "data": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "per_page": per_page
        }
    except Exception as e:
        logger.error(f"Error getting paginated local vehicles: {e}")
        return {"data": [], "total": 0, "page": page, "per_page": per_page}
    finally:
        conn.close()

