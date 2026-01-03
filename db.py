import sqlite3

DB_NAME = "visitors.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(app=None):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS visitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_number TEXT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    person_to_visit TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    has_vehicle INTEGER DEFAULT 0,
                    vehicle_number TEXT,
                    entry_time TEXT NOT NULL,
                    exit_time TEXT
                )
            ''')
    finally:
        conn.close()