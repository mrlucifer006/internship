
from employee_db import get_all_employees_full
from cache_manager import get_db_connection

print("Testing get_all_employees_full...")
try:
    employees = get_all_employees_full()
    print(f"Count: {len(employees)}")
    print(f"Data: {employees}")
except Exception as e:
    print(f"Error: {e}")

print("\nDirect SQL check:")
conn = get_db_connection()
cursor = conn.execute("SELECT * FROM employee")
rows = cursor.fetchall()
print(f"Total rows in employee table: {len(rows)}")
conn.close()
