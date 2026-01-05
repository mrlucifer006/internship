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
    # Simulate login by setting session
    with client.session_transaction() as sess:
        sess['user'] = 'super'
        sess['auth_level'] = 5
        sess['login_id'] = 'test_user_id'
    
    try:
        print("Attempting to access /logistics_exit")
        response = client.get('/logistics_exit')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print("Captured 500 Error!")
            # Manually trigger it to see traceback if client hides it (though test_client usually propagates exceptions unless configured otherwise)
            # But wait, app.errorhandler(500) catches it and renders template.
            # So we won't see traceback unless we disable error catching or look at what's logged.
            # We can force verify by setting propagate_exceptions
        else:
            print("Page loaded successfully (unexpected).")
            # print(response.data.decode('utf-8')[:500])
    except Exception as e:
        print(f"Exception caught during request: {e}")
        import traceback
        traceback.print_exc()
