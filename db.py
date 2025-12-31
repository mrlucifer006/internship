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
            
            # Migration for existing table: Attempt to add the column if it doesn't exist.
            # SQLite doesn't have "IF NOT EXISTS" for ADD COLUMN in older versions, 
            # but we can try catch or check pragma. A try-except block is safest/simplest for dev.
            # Migration for existing table
            try:
                conn.execute('ALTER TABLE visitors ADD COLUMN ticket_number TEXT')
            except sqlite3.OperationalError:
                pass
                
            try:
                # Default to Approved for backward compatibility
                conn.execute("ALTER TABLE visitors ADD COLUMN approval_status TEXT DEFAULT 'Approved'") 
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute("ALTER TABLE visitors ADD COLUMN updated_at DATETIME")
                conn.execute("UPDATE visitors SET updated_at = entry_time WHERE updated_at IS NULL")
            except sqlite3.OperationalError:
                pass

            try:
                conn.execute("ALTER TABLE visitors ADD COLUMN denial_reason TEXT")
            except sqlite3.OperationalError:
                pass
    finally:
        conn.close()
