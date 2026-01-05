import os
import sys
import sqlite3
from flask import Flask, render_template, session

# Add project root to path
sys.path.append(os.getcwd())

from app import app
import vehicle_db # Uses local_cache.db

# Context processor mock
def get_role_name_mock(level):
    return "Admin"

app.jinja_env.globals.update(get_role_name=get_role_name_mock)

# Mock session
with app.test_request_context('/logistics_exit'):
    session['user'] = 'TestUser'
    session['auth_level'] = 5

    try:
        print("Fetching vehicles...")
        vehicles = vehicle_db.get_all_vehicles()
        print(f"Fetched {len(vehicles)} vehicles.")
        
        # Take just 10 like the route does
        recent_vehicles = vehicles[:10] if vehicles else []
        
        print("Rendering template...")
        rendered = render_template('logistics_exit.html', recent_vehicles=recent_vehicles)
        print("Render Success!")
    except Exception as e:
        print(f"\nRender Failed: {e}")
        import traceback
        traceback.print_exc()
