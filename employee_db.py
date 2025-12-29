import sqlite3

DB_NAME = 'employee.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    try:
        conn = get_db_connection()
        with conn:
            conn.execute("CREATE TABLE IF NOT EXISTS employee (name TEXT NOT NULL, phone TEXT NOT NULL, login_id TEXT NOT NULL, password TEXT NOT NULL, Auth_level INT NOT NULL)")
        return True
    except Exception as e:
        print(f"Error creating table: {e}")
        return False
    finally:
        conn.close()

def insert_employee(data):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("INSERT INTO employee (name, phone, login_id, password, Auth_level) VALUES (?, ?, ?, ?, ?)", (data["name"], "+91"+data["phone"], data["login_id"], data["password"], data["Auth_level"]))
            return True
    except Exception as e:
        print(f"Error inserting employee: {e}")
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
        print(f"Error getting employee by name: {e}")
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
                return dict(row)
            else:
                return "Employee not found"
    except Exception as e:
        print(f"Error getting employee phone: {e}")
        return False
    finally:
        conn.close()            

