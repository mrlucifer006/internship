from app import app
import flask

def test_post():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False 
    client = app.test_client()

    print("--- Attempting POST to /data ---")
    data = {
        'name': 'Sanjai', 
        'V_name': 'Debug User',
        'Number': '1234567890',
        'reason': 'Debugging',
        'vehicle': 'on',
        'vehicle_number': 'MH 99 9999'
    }
    
    response = client.post('/data', data=data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 500:
        print("Response Data (Error Message):")
        print(response.data.decode('utf-8'))
    elif response.status_code == 302:
        print(f"Success! Redirected to: {response.location}")
    else:
        print("Response Data:")
        print(response.data.decode('utf-8'))

if __name__ == "__main__":
    test_post()
