import os
import sys
import logging

# Suppress noisy logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Add project root to path
sys.path.append(os.getcwd())

from app import app

# Create a test client
with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user'] = 'super'
        sess['auth_level'] = 5
        sess['login_id'] = 'test_user_id'
    
    try:
        print("Verifying /logistics_exit...")
        response = client.get('/logistics_exit')
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Page loaded correctly.")
            if b'Logistics Exit' in response.data:
                print("Content verified.")
            else:
                print("WARNING: Page loaded but 'Logistics Exit' text not found.")
        else:
            print(f"FAILURE: Status code {response.status_code} (Expected 200)")
            
    except Exception as e:
        print(f"Exception caught: {e}")
