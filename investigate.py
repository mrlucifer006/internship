import requests
import sqlite3
import os

# 1. Check Running Server
try:
    print("Checking http://localhost:5000/logistics_exit...")
    # We might need cookies for login?
    # If we don't have cookies, it will redirect to login (302), which is NOT 500.
    # If we get 500 without login, that's interesting.
    # But likely we get 302.
    # We can try to login first.
    
    session = requests.Session()
    # Assuming standard login form
    # But we don't know the password for 'super' (app.py says 'password123' at line 111)
    
    login_url = 'http://localhost:5000/login'
    login_data = {'username': 'super', 'password': 'password123'}
    
    print("Logging in as super...")
    r_login = session.post(login_url, data=login_data)
    print(f"Login Response: {r_login.status_code}")
    
    if r_login.status_code == 200 and 'Dashboard' in r_login.text or 'Logistics' in r_login.text:
         print("Login successful.")
         
         print("Accessing /logistics_exit...")
         r_page = session.get('http://localhost:5000/logistics_exit')
         print(f"Page Response: {r_page.status_code}")
         if r_page.status_code == 500:
             print("CONFIRMED 500 ERROR on running server.")
         else:
             print("Could not reproduce 500 on running server (got {r_page.status_code}).")
    else:
        print("Login failed or redirected unexpectedly.")

except Exception as e:
    print(f"Server check failed: {e}")

# 2. Dump DB
print("\nDumping Vehicle Table from local_cache.db:")
try:
    if os.path.exists('local_cache.db'):
        conn = sqlite3.connect('local_cache.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM vehicle LIMIT 5')
        rows = cursor.fetchall()
        for row in rows:
            print(dict(row))
        conn.close()
    else:
        print("local_cache.db not found.")
except Exception as e:
    print(f"DB Dump failed: {e}")
