
from employee_db import update_employee_status, get_db_connection
import time

def verify_status_toggle():
    conn = get_db_connection()
    # Create a test user if not exists
    try:
        conn.execute("INSERT INTO employee (name, login_id, phone, password, Auth_level, status) VALUES ('StatusTester', 'statustest', '5555555555', 'pass', 1, 1)")
        print("Created test user 'StatusTester'")
    except:
        print("Test user might already exist, proceeding...")
    
    # Force set to Online (1)
    update_employee_status('statustest', 1)
    
    # Verify Online
    row = conn.execute("SELECT status FROM employee WHERE login_id = 'statustest'").fetchone()
    print(f"Initial Status (should be 1): {row['status']}")
    if row['status'] != 1:
        print("FAIL: Could not set status to 1")
        return

    # Simulate Logout - Set to Offline (0)
    print("Simulating Logout...")
    update_employee_status('statustest', 0)
    
    # Verify Offline
    row = conn.execute("SELECT status FROM employee WHERE login_id = 'statustest'").fetchone()
    print(f"Post-Logout Status (should be 0): {row['status']}")
    
    if row['status'] == 0:
        print("PASS: Status successfully updated to 0 (Offline)")
    else:
        print(f"FAIL: Status remains {row['status']}")

    # Cleanup
    conn.execute("DELETE FROM employee WHERE login_id = 'statustest'")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    verify_status_toggle()
