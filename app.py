import flask
import threading
import time
from datetime import timedelta
import atexit
from Whatsapp_message import send_message
from db import init_db
from visitor_service import save_visitor, get_all_entries, check_out_visitor, get_active_visitors, get_latest_visitor_timestamp
from employee_db import get_employee_phone, check_credentials, insert_employee, update_employee_status, add_notification, get_employee_by_name, get_unread_notifications, get_all_employees, reset_all_employee_statuses
import os


app = flask.Flask(__name__)
app.secret_key = 'super_secret_key_for_demo' # Required for flash messages
app.permanent_session_lifetime = timedelta(hours=24)

# Initialize DB
init_db()

# Reset statuses on exit
atexit.register(reset_all_employee_statuses)

# Helper: Check if logged in
def is_logged_in():
    return 'user' in flask.session

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        username = flask.request.form.get('username')
        password = flask.request.form.get('password')
        
        # Check DB first
        user = check_credentials(username, password)
        if user:
            flask.session.permanent = True
            flask.session['user'] = user['name']
            flask.session['auth_level'] = user['Auth_level'] # Store auth level
            flask.session['login_id'] = user['login_id']
            # Explicitly set to 1 (integer)
            update_employee_status(user['login_id'], 1)
            return flask.redirect(flask.url_for('home'))

        # Fallback: Simple Hardcoded Credentials (ADMIN)
        if username == 'super' and password == 'password123':
            flask.session.permanent = True
            flask.session['user'] = username
            flask.session['auth_level'] = 5 # Grant max authority to hardcoded admin
            return flask.redirect(flask.url_for('home'))
        else:
            flask.flash("Invalid credentials. Please try again.", 'error')
            
    return flask.render_template('login.html')

@app.route('/logout')
def logout():
    login_id = flask.session.get('login_id')
    if login_id:
        # Explicitly set to 0 (integer)
        update_employee_status(login_id, 0)
    
    flask.session.pop('user', None)
    flask.session.pop('auth_level', None)
    flask.session.pop('login_id', None)
    return flask.redirect(flask.url_for('login'))

@app.route('/')
def index():
    return flask.redirect(flask.url_for('login'))

@app.route('/home')
def home ():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    entries = get_all_entries() # For now, showing all. Could be recent.
    employees = get_all_employees()
    return flask.render_template('home.html', entries=entries, employees=employees)

@app.route('/data',methods=['GET','POST'])
def get_data():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    try:
        if flask.request.method == 'POST':
            print(f"\nDEBUG: Received Form Data: {dict(flask.request.form)}") # DEBUG: Check what is actually received
            name = flask.request.form.get('name')
            if not name:
                 flask.flash("Host Name is required.", 'error')
                 return flask.redirect(flask.url_for('home'))

            # Lookup Host Phone
            host_number = get_employee_phone(name)
            if not host_number:
                flask.flash(f"Host '{name}' not found in Employee Database.", 'error')
                return flask.redirect(flask.url_for('home'))
                
            Number = flask.request.form.get('Number')
            V_name = flask.request.form.get('V_name')
            reason = flask.request.form.get('reason')
            vehicle = flask.request.form.get('vehicle')
            vehicle_number = None
            if vehicle:
                vehicle_number = flask.request.form.get('vehicle_number')
    # --- CHECK HOST STATUS ---
            from employee_db import get_employee_by_name, add_notification
            host_info = get_employee_by_name({'name': name}) # name is Host Name
            
            approval_status = "Approved" # Default
            is_host_online = False
            
            if host_info and host_info != "Employee not found":
                if host_info.get('status'): # If Host is Online (1)
                    approval_status = "Pending"
                    is_host_online = True

            data = {
                "name": name,
                "Number": Number, # Assuming 'Number' is visitor's phone
                "V_name": V_name,
                "reason": reason,
                "vehicle": vehicle,
                "vehicle_number": vehicle_number,
                "approval_status": approval_status
            }
            
            result = save_visitor(data)
            
            if result["success"]:
                # Send Notification if Host is Online and status is Pending
                if is_host_online and result.get("visitor_id"):
                     add_notification(host_info['login_id'], V_name, reason, visitor_id=result["visitor_id"])
                     if approval_status == "Pending":
                         flask.flash("Visitor entry pending. Waiting for Host approval.", 'warning')
                     else:
                         flask.flash("Visitor entry logged successfully!", 'success')
                else:
                    # Host is Offline: Send WhatsApp and Notify Guard
                    if host_info and host_info != "Employee not found":
                        from Whatsapp_message import send_message
                        import threading
                        
                        host_phone = host_info['phone'] 
                        # Function to run in thread
                        def send_wa():
                            try:
                                print(f"Sending WhatsApp to {host_info['name']} at {host_phone}")
                                send_message(V_name, Number, reason, host_info['name'], host_phone)
                            except Exception as e:
                                print(f"WhatsApp Error: {e}")
                                
                        threading.Thread(target=send_wa).start()
                        
                        flask.flash(f"Host '{host_info['name']}' is Offline. Notification sent via WhatsApp.", 'success')
                        flask.render_template('check_out.html', visitors=get_all_entries())
                        time.sleep(2)
                    else:
                        flask.flash("Visitor entry logged successfully! (Host not found)", 'success')
                        flask.render_template('check_out.html', visitors=get_all_entries())
                        time.sleep(2)
                return flask.redirect(flask.url_for('home'))
            else:
                for err in result["errors"]:
                    flask.flash(err, 'error')
                return flask.redirect(flask.url_for('home'))
            
        return flask.redirect(flask.url_for('home'))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Internal Server Error: {e}", 500

@app.route('/entry_data',methods = ['GET','POST'])
def entry_data():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    name = flask.request.args.get('name')
    Number = flask.request.args.get('Number')
    host_number = flask.request.args.get('host_number')
    V_name = flask.request.args.get('V_name')
    reason = flask.request.args.get('reason')
    vehicle = flask.request.args.get('vehicle')
    vehicle_number = flask.request.args.get('vehicle_number')
    
    
    # Check Host Status
    host = get_employee_by_name({"name": name})
    
    # If host is found and is Online (status=1), send internal notification
    if host and host.get('status') == 1:
        print(f"Host {name} is Online. Sending Popup Notification.")
        add_notification(host['login_id'], V_name, reason)
        
    else:
        # Host is Offline or not found (fallback), send WhatsApp
        print(f"Host {name} is Offline. Sending WhatsApp.")
        def send_notification():
            try:
                # Send message to Host (host_number), about Visitor (V_name)
                send_message(V_name, Number, reason, name, host_number) 
            except Exception as e:
                print(f"Failed to send WhatsApp: {e}")

        threading.Thread(target=send_notification).start()
    
    return flask.render_template('entry_data.html', name=name, Number=Number, V_name=V_name, reason=reason, vehicle=vehicle, vehicle_number=vehicle_number)
@app.route('/view_all')
def view_all():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    return flask.render_template('view_all.html', entries=get_all_entries())

@app.route('/check_out_page')
def check_out_page():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    active_visitors = get_active_visitors()
    return flask.render_template('check_out.html', visitors=active_visitors)

@app.route('/process_check_out', methods=['POST'])
def process_check_out():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    visitor_name = flask.request.form.get('visitor_name')
    phone = flask.request.form.get('phone')
    
    if not visitor_name or not phone:
        flask.flash("Missing visitor details for check-out.", 'error')
        return flask.redirect(flask.url_for('check_out_page'))
        
    result = check_out_visitor(visitor_name, phone)
    if result['success']:
        flask.flash(f"Visitor {visitor_name} checked out successfully.", 'success')
    else:
        for error in result.get('errors', []):
            flask.flash(error, 'error')
            
    return flask.redirect(flask.url_for('check_out_page'))

@app.route('/new_user')
def new_user():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    
    # Check Authority
    if flask.session.get('auth_level', 0) < 5:
        flask.flash("You do not have authority to access this page.", 'error')
        return flask.redirect(flask.url_for('home'))
        
    return flask.render_template('new_user.html')

@app.route('/process_add_user', methods=['POST'])
def process_add_user():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    if flask.session.get('auth_level', 0) < 5:
        flask.flash("Unauthorized action.", 'error')
        return flask.redirect(flask.url_for('home'))

    name = flask.request.form.get('name')
    login_id = flask.request.form.get('login_id')
    phone = flask.request.form.get('phone')
    password = flask.request.form.get('password')
    # Slider/Input might give string '3'
    try:
        auth_level = int(flask.request.form.get('auth_level', 1))
    except:
        auth_level = 1
        
    if not all([name, login_id, phone, password]):
        flask.flash("All fields are required.", 'error')
        return flask.redirect(flask.url_for('new_user'))
        
    data = {
        "name": name.strip(),
        "login_id": login_id.strip(),
        "phone": phone.replace("+91", "").strip(), 
        "password": password,
        "Auth_level": auth_level,
        "status": 0
    }
    
    if insert_employee(data):
        flask.flash(f"User {name} added successfully!", 'success')
        return flask.redirect(flask.url_for('home'))
    else:
        flask.flash("Failed to add user. Login ID might be taken.", 'error')
        return flask.redirect(flask.url_for('new_user'))

    
@app.route('/check_notifications')
def check_notifications():
    if not is_logged_in():
        return flask.jsonify([])
        
    login_id = flask.session.get('login_id')
    if not login_id:
        return flask.jsonify([])
        
    notifications = get_unread_notifications(login_id)
    return flask.jsonify(notifications)

@app.route('/check_updates')
def check_updates():
    if not is_logged_in():
        return flask.jsonify({'last_updated': None})
    
    last_updated = get_latest_visitor_timestamp()
    return flask.jsonify({'last_updated': last_updated})

@app.route('/view_status')
def view_status():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    if flask.session.get('auth_level', 0) < 4:
        flask.flash("Unauthorized access.", 'error')
        return flask.redirect(flask.url_for('home'))
        
    from employee_db import get_all_employees_full
    employees = get_all_employees_full()
    return flask.render_template('view_status.html', employees=employees)

@app.route('/api/employees')
def api_employees():
    if not is_logged_in():
        return flask.jsonify({'error': 'Unauthorized'}), 401
    
    if flask.session.get('auth_level', 0) < 4:
        return flask.jsonify({'error': 'Unauthorized'}), 403
        
    from employee_db import get_all_employees_full
    employees = get_all_employees_full()
    employees = get_all_employees_full()
    return flask.jsonify(employees)

@app.route('/notifications')
def notifications_page():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    login_id = flask.session.get('login_id')
    from employee_db import get_notification_history
    notifications = get_notification_history(login_id)
    
    # render the template with the latest notification if exists
    latest_notification = notifications[0] if notifications else None
    
    return flask.render_template('notification.html', notification=latest_notification, all_notifications=notifications)

@app.route('/api/visitors')
def get_visitors_api():
    if not is_logged_in():
        return flask.jsonify({'error': 'Unauthorized'}), 401
    
    visitors = get_active_visitors()
    return flask.jsonify(visitors)

@app.route('/api/action_visitor', methods=['POST'])
def action_visitor():
    if not is_logged_in():
        return flask.jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    data = flask.request.get_json()
    visitor_id = data.get('visitor_id')
    action = data.get('action') # 'approve' or 'deny'
    
    if not visitor_id or not action:
        return flask.jsonify({'success': False, 'error': 'Missing data'})
        
    status = "Approved" if action == 'approve' else "Denied"
    
    from db import get_db_connection
    conn = get_db_connection()
    try:
        with conn:
            # If Denied, we might want to set exit_time immediately so they aren't 'active'?
            # Or just set status. User said "not update entry" which implies "don't let them in".
            # For logging purposes, 'Denied' status is good.
            from datetime import datetime
            now = datetime.now().isoformat()
            
            # Update status and updated_at. Do NOT set exit_time yet, so Guard sees the feedback.
            if action == 'deny':
                reason = data.get('reason', '')
                conn.execute("UPDATE visitors SET approval_status = ?, updated_at = ?, denial_reason = ? WHERE id = ?", (status, now, reason, visitor_id))
            else:
                 conn.execute("UPDATE visitors SET approval_status = ?, updated_at = ? WHERE id = ?", (status, now, visitor_id))
            
        return flask.jsonify({'success': True, 'status': status})
    except Exception as e:
        return flask.jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

if __name__ == '__main__':
    from employee_db import create_table as create_employee_table
    # Ensure DBs exist
    init_db()
    create_employee_table()

    import socket
    try:
        # Determine local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        print(f"\nExample App running on: http://{ip_address}:5000\n")
    except Exception as e:
        print(f"Could not determine IP: {e}")
    
    app.run(host='0.0.0.0',port=5000,debug=True)