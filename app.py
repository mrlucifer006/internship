import flask
import threading
import time
import os
import atexit
import logging
from datetime import timedelta

# Import configuration and logging
from config import get_config
from logging_config import setup_logging

# Import database modules
from db import init_db
import vehicle_db

# Import services
from visitor_service import save_visitor, get_all_entries, check_out_visitor, get_active_visitors, get_latest_visitor_timestamp, get_entries_paginated
from employee_db import (
    get_employee_phone, check_credentials, insert_employee, 
    update_employee_status, add_notification, get_employee_by_name, 
    get_unread_notifications, get_all_employees, reset_all_employee_statuses, 
    get_employee_status
)

# Import messaging modules
from Whatsapp_message import send_message
import Logistics_message

# Initialize Flask app
app = flask.Flask(__name__)

# Load configuration
config_obj = get_config()
app.config.from_object(config_obj)
app.secret_key = config_obj.SECRET_KEY
app.permanent_session_lifetime = config_obj.PERMANENT_SESSION_LIFETIME

# Setup logging
setup_logging(app, config_obj.LOG_LEVEL, config_obj.LOG_FILE)
logger = logging.getLogger(__name__)

# Log configuration warnings
warnings = config_obj.validate()
for warning in warnings:
    logger.warning(warning)



# Reset statuses on exit
atexit.register(reset_all_employee_statuses)

@app.context_processor
def inject_role_name():
    def get_role_name(level):
        if level is None: return 'Unknown'
        roles = {
            1: 'Foreman',
            2: 'Supervisor',
            3: 'Employee',
            4: 'Admin',
            5: 'Developer'
        }
        return roles.get(int(level), 'Unknown')
    return dict(get_role_name=get_role_name)

def is_logged_in():
    if 'user' not in flask.session:
        return False
    
    # STRICT CHECK: Verify status in DB is still 1
    # Skip check for hardcoded 'super' admin
    if flask.session.get('user') == 'super':
        return True
        
    login_id = flask.session.get('login_id')
    if not login_id:
         return False # Should have login_id if not super
         
    status = get_employee_status(login_id)
    # If status is 0 (or None/Error), force logout
    if status != 1: 
        # Perform logout cleanup
        flask.session.pop('user', None)
        flask.session.pop('auth_level', None)
        flask.session.pop('login_id', None)
        return False
        
    return True

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

def get_base_path():
    """Get the persistent base path for file storage (works for both script and exe)."""
    import sys
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serve uploaded files from the persistent uploads directory."""
    upload_dir = os.path.join(get_base_path(), 'uploads')
    return flask.send_from_directory(upload_dir, filename)

@app.route('/')
def index():
    return flask.redirect(flask.url_for('login'))

@app.route('/home')
def home():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    page = flask.request.args.get('page', 1, type=int)
    per_page = 10 # Default to 10 for sidebar list
    
    # Use paginated fetching
    pagination = get_entries_paginated(page=page, per_page=per_page)
    entries = pagination.data # For backward compatibility if templates use 'entries' directly
    
    employees = get_all_employees()
    return flask.render_template('home.html', entries=entries, employees=employees, pagination=pagination)

@app.route('/data',methods=['GET','POST'])
def get_data():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    try:
        if flask.request.method == 'POST':
            logger.debug(f"Received Form Data: {dict(flask.request.form)}")
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
                                logger.info(f"Sending WhatsApp to {host_info['name']} at {host_phone}")
                                send_message(V_name, Number, reason, host_info['name'], host_phone)
                            except Exception as e:
                                logger.error(f"WhatsApp Error: {e}")
                                
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
        logger.exception("Error processing visitor data")
        flask.flash("An internal error occurred. Please try again.", 'error')
        return flask.redirect(flask.url_for('home'))

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
        logger.info(f"Host {name} is Online. Sending Popup Notification.")
        add_notification(host['login_id'], V_name, reason)
        
    else:
        # Host is Offline or not found (fallback), send WhatsApp
        logger.info(f"Host {name} is Offline. Sending WhatsApp.")
        def send_notification():
            try:
                # Send message to Host (host_number), about Visitor (V_name)
                send_message(V_name, Number, reason, name, host_number) 
            except Exception as e:
                logger.error(f"Failed to send WhatsApp: {e}")

        threading.Thread(target=send_notification).start()
    
    return flask.render_template('entry_data.html', name=name, Number=Number, V_name=V_name, reason=reason, vehicle=vehicle, vehicle_number=vehicle_number)
@app.route('/view_all')
def view_all():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    # Restrict to Admin (4) and Super (5). Foreman (3) and others cannot view.
    if flask.session.get('auth_level', 0) < 4:
        flask.flash("You do not have authority to access this page.", 'error')
        return flask.redirect(flask.url_for('home'))
        
    return flask.render_template('view_all.html', entries=get_all_entries())

@app.route('/logistics')
def logistics():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    
    # Fetch recent vehicle entries
    recent_vehicles = vehicle_db.get_all_vehicles()
    # Optionally limit to the last 10 or so for the sidebar
    recent_vehicles = recent_vehicles[:10] if recent_vehicles else []

    return flask.render_template('logistics_entry.html', recent_vehicles=recent_vehicles)

@app.route('/logistics_exit')
def logistics_exit():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    
    # Fetch recent vehicle entries (same as entry mostly)
    recent_vehicles = vehicle_db.get_all_vehicles()
    recent_vehicles = recent_vehicles[:10] if recent_vehicles else []

    return flask.render_template('logistics_exit.html', recent_vehicles=recent_vehicles)

@app.route('/process_logistics_entry', methods=['POST'])
def process_logistics_entry():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))

    try:
        # 1. Handle File Upload
        photo_filename = None
        if 'vehicle_photo' in flask.request.files:
            file = flask.request.files['vehicle_photo']
            if file and file.filename != '':
                # Use persistent path next to the executable (not temp folder)
                upload_folder = os.path.join(get_base_path(), 'uploads', 'vehicles')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Secure filename and save
                # For simplicity, using timestamp to avoid overwrites
                import time
                ext = os.path.splitext(file.filename)[1]
                timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
                safe_name = f"veh_{timestamp}{ext}"
                file.save(os.path.join(upload_folder, safe_name))
                photo_filename = safe_name

        # 2. Extract Data
        data = {
            "driver_name": flask.request.form.get('driver_name'),
            "driver_phone": flask.request.form.get('driver_phone'),
            "veh_reg_no": flask.request.form.get('vehicle_number').upper(),
            "origin": flask.request.form.get('loc_from'),
            "destination": flask.request.form.get('loc_to'),
            "vehicle_img": photo_filename,
            "entry_type": "Entry"
        }

        # 3. Insert into DB
        if vehicle_db.insert_vehicle(data):
            # 4. Send WhatsApp Notification (Async)
            try:
                # Get the full path to the uploaded image
                vehicle_img_path = None
                if photo_filename:
                    vehicle_img_path = os.path.join(get_base_path(), 'uploads', 'vehicles', photo_filename)
                
                def send_notification():
                    Logistics_message.send_whatsapp_message(
                        driver_name=data["driver_name"],
                        driver_phone=data["driver_phone"],
                        vehicle_number=data["veh_reg_no"],
                        from_location=data["origin"],
                        to_location=data["destination"],
                        vehicle_img_path=vehicle_img_path
                    )
                
                threading.Thread(target=send_notification).start()
            except Exception as e:
                print(f"Error starting WhatsApp thread: {e}")

            flask.flash("Logistics entry recorded successfully!", "success")
        else:
            flask.flash("Failed to record entry. Vehicle number may already exist.", "error")

    except Exception as e:
        print(f"Error processing logistics entry: {e}")
        flask.flash("An error occurred while processing the entry.", "error")

    return flask.redirect(flask.url_for('logistics'))

@app.route('/process_logistics_exit', methods=['POST'])
def process_logistics_exit():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))

    try:
        # 1. Handle File Upload
        photo_filename = None
        if 'vehicle_photo' in flask.request.files:
            file = flask.request.files['vehicle_photo']
            if file and file.filename != '':
                # Use persistent path next to the executable (not temp folder)
                upload_folder = os.path.join(get_base_path(), 'uploads', 'vehicles')
                os.makedirs(upload_folder, exist_ok=True)
                import time
                ext = os.path.splitext(file.filename)[1]
                timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
                safe_name = f"veh_exit_{timestamp}{ext}"
                file.save(os.path.join(upload_folder, safe_name))
                photo_filename = safe_name

        # 2. Extract Data
        data = {
            "driver_name": flask.request.form.get('driver_name'),
            "driver_phone": flask.request.form.get('driver_phone'),
            "veh_reg_no": flask.request.form.get('vehicle_number').upper(),
            "origin": flask.request.form.get('loc_from'),
            "destination": flask.request.form.get('loc_to'),
            "purchase_no": flask.request.form.get('purchase_number'),
            "vehicle_img": photo_filename,
            "entry_type": "Exit"
        }

        # 3. Insert into DB (inserts new record for history)
        if vehicle_db.insert_vehicle(data):
            # 4. Send WhatsApp Notification (Async)
            try:
                # Get the full path to the uploaded image
                vehicle_img_path = None
                if photo_filename:
                    vehicle_img_path = os.path.join(get_base_path(), 'uploads', 'vehicles', photo_filename)
                
                def send_notification():
                    Logistics_message.in_message(
                        driver_name=data["driver_name"],
                        driver_phone=data["driver_phone"],
                        vehicle_number=data["veh_reg_no"],
                        po_number=data.get("purchase_no", ""),
                        from_location=data["origin"],
                        to_location=data["destination"],
                        vehicle_img_path=vehicle_img_path
                    )
                
                threading.Thread(target=send_notification).start()
            except Exception as e:
                print(f"Error starting WhatsApp thread: {e}")
            
            flask.flash("Logistics exit recorded successfully!", "success")
        else:
            flask.flash("Failed to record exit.", "error")

    except Exception as e:
        print(f"Error processing logistics exit: {e}")
        flask.flash("An error occurred while processing the exit.", "error")

    return flask.redirect(flask.url_for('logistics_exit'))

@app.route('/view_all_logistics')
def view_all_logistics():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    
    # Get pagination parameters
    page = flask.request.args.get('page', 1, type=int)
    per_page = flask.request.args.get('per_page', 50, type=int)
    search = flask.request.args.get('search', None, type=str)
    
    # Fetch paginated vehicle entries
    result = vehicle_db.get_vehicles_paginated(page=page, per_page=per_page, search=search)
    
    return flask.render_template(
        'view_all_logistics.html', 
        vehicles=result.data,
        pagination=result,
        search=search or ''
    )

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
    
    logger.debug(f"process_check_out called with name='{visitor_name}', phone='{phone}'")

    if not visitor_name or not phone:
        logger.warning("Missing visitor details for check-out")
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
    
    # Check Authority (Now Level 4+)
    if flask.session.get('auth_level', 0) < 4:
        flask.flash("You do not have authority to access this page.", 'error')
        return flask.redirect(flask.url_for('home'))
        
    return flask.render_template('new_user.html')

@app.route('/process_add_user', methods=['POST'])
def process_add_user():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    if flask.session.get('auth_level', 0) < 4:
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
    
    from employee_db import get_all_employees_full
    employees = get_all_employees_full()
    return flask.jsonify(employees)

@app.route('/delete_user/<login_id>', methods=['POST'])
def delete_user(login_id):
    if 'user' not in flask.session:
        return flask.redirect(flask.url_for('login'))
        
    # Check Auth Level (Must be 4 or higher)
    auth_level = flask.session.get('auth_level', 0)
    if auth_level < 4:
        flask.flash('You do not have permission to delete users.', 'error')
        return flask.redirect(flask.url_for('view_status'))
        
    from employee_db import delete_employee
    
    if 'login_id' in flask.session and flask.session['login_id'] == login_id:
        flask.flash('You cannot delete your own account.', 'error')
        return flask.redirect(flask.url_for('view_status'))

    if delete_employee(login_id):
        flask.flash(f'User {login_id} deleted successfully.', 'success')
    else:
        flask.flash(f'Failed to delete user {login_id}.', 'error')
        
    return flask.redirect(flask.url_for('view_status'))
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

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring and container orchestration."""
    try:
        # Test database connectivity
        from db import get_db_connection
        conn = get_db_connection()
        conn.execute('SELECT 1').fetchone()
        conn.close()
        
        return flask.jsonify({
            'status': 'healthy',
            'service': 'visitor_management',
            'timestamp': time.time()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return flask.jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    if flask.request.path.startswith('/api/'):
        return flask.jsonify({'error': 'Not found'}), 404
    return flask.render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.exception("Internal server error")
    if flask.request.path.startswith('/api/'):
        return flask.jsonify({'error': 'Internal server error'}), 500
    return flask.render_template('errors/500.html'), 500


@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors."""
    if flask.request.path.startswith('/api/'):
        return flask.jsonify({'error': 'Forbidden'}), 403
    return flask.render_template('errors/403.html'), 403


# Register SEO routes blueprint
from seo_routes import seo_bp
app.register_blueprint(seo_bp)


def initialize_application():
    """Performs startup tasks: DB check."""
    logger.info(f"Initializing application with Supabase backend.")
    
    # Initialize connection check
    init_db()
    
    # VERIFY TABLE CREATION
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employee'")
        if cursor.fetchone():
            logger.info("Database tables verified successfully.")
        else:
            logger.error("! Critical: 'employee' table verification failed after initialization.")
        conn.close()
    except Exception as e:
        logger.error(f"! Database verification failed: {e}")
    
    # --- AUTO-BACKUP ON STARTUP ---
    try:
        backup_manager = DatabaseBackup(db_path=DB_NAME)
        backup_path = backup_manager.create_backup()
        logger.info(f"[SUCCESS] Startup backup created: {backup_path}")
        print(f"OK Startup backup created: {backup_path.name}")
    except Exception as e:
        logger.error(f"Startup backup failed: {e}")
        print(f"! Startup backup failed: {e}")
    
    logger.info("Database initialization complete")


if __name__ == '__main__':
    
    # Initialize App Logic
    initialize_application()

    # Replaced localized create_table calls with init_db() above
    # create_employee_table() # Removed
    # vehicle_db.create_table() # Removed
    
    logger.info("Database initialization complete")

    import socket
    try:
        # Determine local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        logger.info(f"Starting server on http://{ip_address}:{config_obj.PORT}")
        print(f"\n🚀 Visitor Management System running on: http://{ip_address}:{config_obj.PORT}\n")
    except Exception as e:
        logger.warning(f"Could not determine IP: {e}")
        print(f"\n🚀 Visitor Management System running on: http://localhost:{config_obj.PORT}\n")
    
    try:
        app.run(
            host=config_obj.HOST,
            port=config_obj.PORT,
            debug=config_obj.DEBUG
        )
    except Exception as e:
        logger.exception("Application crashed")
        print(f"CRITICAL ERROR: {e}")
    finally:
        print("\nApplication exiting. Terminal will close in 10 seconds...")
        time.sleep(10)