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
                id_type TEXT,
                id_number TEXT,
                updated_at TEXT,
                created_at TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicle (
                id INTEGER PRIMARY KEY,
                driver_name TEXT,
                veh_reg_no TEXT,
                vehicle_img TEXT,
                destination TEXT,
                "time" TEXT,
                driver_phone TEXT,
                origin TEXT,
                purchase_no TEXT,
                entry_type TEXT,
                is_returnable INTEGER DEFAULT 0,
                material_type TEXT,
                return_reason TEXT,
                created_at TEXT
            )
        ''')
        
        # Migration: Add new columns if they don't exist (for existing DBs)
        try:
            conn.execute('ALTER TABLE visitors ADD COLUMN id_type TEXT')
        except sqlite3.OperationalError:
            pass # Column likely exists
            
        try:
            conn.execute('ALTER TABLE visitors ADD COLUMN id_number TEXT')
        except sqlite3.OperationalError:
            pass # Column likely exists

        # Migration: Add new vehicle columns
        try:
            conn.execute('ALTER TABLE vehicle ADD COLUMN is_returnable INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
            
        try:
            conn.execute('ALTER TABLE vehicle ADD COLUMN material_type TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            conn.execute('ALTER TABLE vehicle ADD COLUMN return_reason TEXT')
        except sqlite3.OperationalError:
            pass

        # [NEW] Add driver_id and length columns
        try:
            conn.execute('ALTER TABLE vehicle ADD COLUMN driver_id_type TEXT')
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute('ALTER TABLE vehicle ADD COLUMN driver_id_number TEXT')
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute('ALTER TABLE vehicle ADD COLUMN vehicle_length TEXT')
        except sqlite3.OperationalError:
            pass

        # Migration: Remove UNIQUE constraint on veh_reg_no (by recreating table)
        # This is complex in SQLite, so we check if constraint exists by trying to insert a duplicate
        # If it fails, we need to migrate. For now, we'll use a simpler check:
        # We'll just rely on the fact that if we change the schema above, new DBs are fine.
        # For existing DBs, we should probably recreate the table to be safe, but that wipes data.
        # A better approach for this session is to rename and copy.
        
        # Check if we need to migrate (this is a heuristic, but effective for dev)
        cursor = conn.execute("PRAGMA index_list('vehicle')")
        indices = cursor.fetchall()
        has_unique_reg = any(i[2] == 1 for i in indices if 'autoindex' in i[1] or 'unique' in i[1])

        # If we suspect a unique constraint (or just force it for this update)
        # Let's force a migration to ensure the constraint is gone.
        # We will check if we have already migrated by checking a flag table or just TRYING.
        # Since we don't have a migration table, we will attempt to drop the index if it's named 'sqlite_autoindex_vehicle_1'
        # But UNIQUE constraints on columns create implicit indices.
        
        # OFFICAL WAY: Create new table, copy data, drop old, rename new.
        # We only do this if we haven't done it yet.
        # Let's check schema details.
        
        table_info = conn.execute("PRAGMA table_info('vehicle')").fetchall()
        # In PRAGMA table_info, pk is col 5. valid is not there.
        # It's hard to detect the constraint easily without parsing SQL from sqlite_master.
        
        schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='vehicle'").fetchone()
        if schema and 'UNIQUE' in schema[0]:
            logger.info("Migrating vehicle table to remove UNIQUE constraint...")
            conn.execute("ALTER TABLE vehicle RENAME TO vehicle_old")
            conn.execute('''
                CREATE TABLE vehicle (
                    id INTEGER PRIMARY KEY,
                    driver_name TEXT,
                    veh_reg_no TEXT,
                    vehicle_img TEXT,
                    destination TEXT,
                    "time" TEXT,
                    driver_phone TEXT,
                    origin TEXT,
                    purchase_no TEXT,
                    entry_type TEXT,
                    is_returnable INTEGER DEFAULT 0,
                    material_type TEXT,
                    return_reason TEXT,
                    created_at TEXT
                )
            ''')
            conn.execute('''
                INSERT INTO vehicle (id, driver_name, veh_reg_no, vehicle_img, destination, "time", driver_phone, origin, purchase_no, entry_type, is_returnable, material_type, return_reason, created_at)
                SELECT id, driver_name, veh_reg_no, vehicle_img, destination, "time", driver_phone, origin, purchase_no, entry_type, is_returnable, material_type, return_reason, created_at
                FROM vehicle_old
            ''')
            conn.execute("DROP TABLE vehicle_old")
            logger.info("Vehicle table migration complete.")

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
        conn.execute('DELETE FROM employee') # Clear local table first (Handles deletions)
        if employees:
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
        conn.execute('DELETE FROM visitors') # Clear local table first (Handles deletions)
        if visitors:
            for v in visitors:
                conn.execute('''
                    INSERT INTO visitors (id, name, phone, person_to_visit, reason, has_vehicle, vehicle_number, entry_time, exit_time, status, denial_reason, id_type, id_number, updated_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    v.get('id_type'),
                    v.get('id_number'),
                    v.get('updated_at'),
                    v.get('created_at')
                ))

        # Sync vehicles
        vehicles = supabase.table('vehicle').select('*').execute().data
        conn.execute('DELETE FROM vehicle') # Clear local table first (Handles deletions)
        if vehicles:
            for v in vehicles:
                conn.execute('''
                    INSERT INTO vehicle (id, driver_name, veh_reg_no, vehicle_img, destination, "time", driver_phone, origin, purchase_no, entry_type, is_returnable, material_type, return_reason, created_at, driver_id_type, driver_id_number, vehicle_length)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    v.get('is_returnable', 0),
                    v.get('material_type'),
                    v.get('return_reason'),
                    v.get('created_at'),
                    v.get('driver_id_type'),
                    v.get('driver_id_number'),
                    v.get('vehicle_length')
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
                    SET name=?, phone=?, person_to_visit=?, reason=?, has_vehicle=?, vehicle_number=?, entry_time=?, exit_time=?, status=?, denial_reason=?, id_type=?, id_number=?, updated_at=?, created_at=?
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
                    data.get('id_type'),
                    data.get('id_number'),
                    data.get('updated_at'),
                    data.get('created_at'),
                    data.get('id')
                ))
        else:
            conn.execute('''
                INSERT INTO visitors (id, name, phone, person_to_visit, reason, has_vehicle, vehicle_number, entry_time, exit_time, status, denial_reason, id_type, id_number, updated_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                data.get('id_type'),
                data.get('id_number'),
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
                SET driver_name=?, veh_reg_no=?, vehicle_img=?, destination=?, "time"=?, driver_phone=?, origin=?, purchase_no=?, entry_type=?, is_returnable=?, material_type=?, return_reason=?, created_at=?, driver_id_type=?, driver_id_number=?, vehicle_length=?
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
                data.get('is_returnable', 0),
                data.get('material_type'),
                data.get('return_reason'),
                data.get('created_at'),
                data.get('driver_id_type'),
                data.get('driver_id_number'),
                data.get('vehicle_length'),
                data.get('id')
            ))
        else:
            conn.execute('''
                INSERT INTO vehicle (id, driver_name, veh_reg_no, vehicle_img, destination, "time", driver_phone, origin, purchase_no, entry_type, is_returnable, material_type, return_reason, created_at, driver_id_type, driver_id_number, vehicle_length)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                data.get('is_returnable', 0),
                data.get('material_type'),
                data.get('return_reason'),
                data.get('created_at'),
                data.get('driver_id_type'),
                data.get('driver_id_number'),
                data.get('vehicle_length')
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

def get_all_local_visitors(search=None, status=None):
    """Retrieve all visitors from the local cache. Optional search and status filter."""
    conn = get_db_connection()
    try:
        query = 'SELECT * FROM visitors WHERE 1=1'
        params = []
        
        if search:
            query += ' AND (name LIKE ? OR phone LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        if status is not None and status != '':
            query += ' AND status = ?'
            params.append(int(status))
            
        query += ' ORDER BY id DESC'
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all local visitors: {e}")
        return []
    finally:
        conn.close()

def get_active_local_visitors(search=None):
    """
    Retrieve all active visitors (not exited) from local cache.
    Optional search by name or phone.
    """
    conn = get_db_connection()
    try:
        query = "SELECT * FROM visitors WHERE exit_time IS NULL AND status = 1"
        params = []
        
        if search:
            search_pattern = f"%{search}%"
            query += " AND (name LIKE ? OR phone LIKE ? OR person_to_visit LIKE ? OR reason LIKE ? OR vehicle_number LIKE ? OR id_number LIKE ?)" 
            params.extend([search_pattern] * 6)
            
        query += " ORDER BY id DESC"
            
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting active local visitors: {e}")
        return []
    finally:
        conn.close()

def get_paginated_local_visitors(page=1, per_page=10, search=None):
    """Retrieve paginated visitors from the local cache. Includes search."""
    conn = get_db_connection()
    try:
        offset = (page - 1) * per_page
        
        # Base Queries
        query = "SELECT * FROM visitors WHERE status != -1"
        count_query = "SELECT COUNT(id) FROM visitors WHERE status != -1"
        params = []
        
        # Search Filter
        if search:
            search_pattern = f"%{search}%"
            query += " AND (name LIKE ? OR phone LIKE ? OR person_to_visit LIKE ? OR reason LIKE ? OR vehicle_number LIKE ? OR id_number LIKE ?)"
            count_query += " AND (name LIKE ? OR phone LIKE ? OR person_to_visit LIKE ? OR reason LIKE ? OR vehicle_number LIKE ? OR id_number LIKE ?)"
            params.extend([search_pattern] * 6)
            
        # Pagination
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        # Count (use search params for count query, not pagination params)
        count_params = [f"%{search}%"] * 6 if search else []
        total_cursor = conn.execute(count_query, count_params)
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
        cursor = conn.execute('SELECT * FROM vehicle ORDER BY id DESC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting all local vehicles: {e}")
        return []
    finally:
        conn.close()

def get_paginated_local_vehicles(page=1, per_page=10, search=None, entry_type=None):
    """Retrieve paginated vehicles from the local cache."""
    conn = get_db_connection()
    try:
        offset = (page - 1) * per_page
        
        query = 'SELECT * FROM vehicle WHERE 1=1'
        count_query = 'SELECT COUNT(id) FROM vehicle WHERE 1=1'
        params = []
        count_params = []
        
        if search:
            search_filter = ' AND (veh_reg_no LIKE ? OR driver_name LIKE ? OR driver_phone LIKE ? OR destination LIKE ? OR origin LIKE ? OR purchase_no LIKE ? OR driver_id_number LIKE ?)'
            query += search_filter
            count_query += search_filter
            search_params = [f'%{search}%'] * 7
            params.extend(search_params)
            count_params.extend(search_params)
        
        if entry_type:
            entry_filter = ' AND entry_type = ?'
            query += entry_filter
            count_query += entry_filter
            params.append(entry_type)
            count_params.append(entry_type)
            
        query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        
        cursor = conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        # Count with filters
        total_cursor = conn.execute(count_query, count_params)
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


