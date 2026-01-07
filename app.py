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
from cache_manager import init_cache, sync_data_from_supabase
from db_supabase import get_supabase_client

# Import services
from visitor_service import save_visitor, get_all_entries, check_out_visitor, get_active_visitors, get_latest_visitor_timestamp, get_entries_paginated, update_visitor_status, get_pending_visitors
from employee_db import (
    get_employee_phone, check_credentials, insert_employee, 
    update_employee_status, get_employee_by_name, 
    get_all_employees, reset_all_employee_statuses, 
    get_employee_status, update_employee_connection
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




# Global variable to track the currently logged-in user in this instance
CURRENT_LOGIN_ID = None

def cleanup_current_user():
    """Reset the status of the currently logged-in user on exit."""
    global CURRENT_LOGIN_ID
    if CURRENT_LOGIN_ID:
        try:
            # We must import here to ensure it's available at exit time if needed, 
            # though usually module scope matches.
            from employee_db import update_employee_status
            print(f"Cleaning up session for user: {CURRENT_LOGIN_ID}")
            update_employee_status(CURRENT_LOGIN_ID, 0)
        except Exception as e:
            print(f"Error during cleanup for {CURRENT_LOGIN_ID}: {e}")

# Register the specific user cleanup instead of the global reset
atexit.register(cleanup_current_user)

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
    global CURRENT_LOGIN_ID
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
            
            # Update global tracker for this instance
            CURRENT_LOGIN_ID = user['login_id']
            
            # --- Detect Connection Mode ---
            try:
                request_ip = flask.request.remote_addr
                
                # Dynamic import to avoid circular dependency issues if any
                from server_discovery import get_local_ip
                server_lan_ip = get_local_ip()
                
                # Check if accessing from Localhost or the Server's own LAN IP
                if request_ip in ['127.0.0.1', 'localhost', '::1', server_lan_ip]:
                    mode = 'Server'
                else:
                    mode = 'Client'
                
                # Update connection info and status=1
                public_url = app.config.get('PUBLIC_URL')
                update_employee_connection(user['login_id'], request_ip, mode, public_url)
                
            except Exception as e:
                logger.error(f"Error updating connection mode: {e}")
                # Fallback to just status update
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
    global CURRENT_LOGIN_ID
    
    login_id = flask.session.get('login_id')
    if login_id:
        # Explicitly set to 0 (integer)
        update_employee_status(login_id, 0)
        
    # Clear global tracker if the logged-out user matches
    if CURRENT_LOGIN_ID == login_id:
        CURRENT_LOGIN_ID = None
    
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
    search = flask.request.args.get('search', '')
    pagination = get_entries_paginated(page=page, per_page=per_page, search=search)

    if flask.request.args.get('ajax'):
        return flask.render_template('partials/sidebar_entries.html', pagination=pagination)

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
            
            # Extract ID Details
            id_type = flask.request.form.get('id_type')
            id_number = flask.request.form.get('id_number')
            
            vehicle = flask.request.form.get('vehicle')
            vehicle_number = None
            if vehicle:
                vehicle_number = flask.request.form.get('vehicle_number')
            # --- CHECK HOST STATUS ---
            from employee_db import get_employee_by_name
            host_info = get_employee_by_name({'name': name}) # name is Host Name
            
            is_host_online = False
            if host_info and host_info != "Employee not found":
                if host_info.get('status'): # If Host is Online (1)
                    is_host_online = True

            data = {
                "name": name,
                "Number": Number, # Assuming 'Number' is visitor's phone
                "V_name": V_name,
                "reason": reason,
                "vehicle": vehicle,
                "vehicle_number": vehicle_number,
                "id_type": id_type,
                "id_number": id_number
            }
            
            result = save_visitor(data)
            
            if result["success"]:
                # Send Notification if Host is Online
                if is_host_online and result.get("visitor_id"):
                     logger.info(f"Host is online. Entry {result.get('visitor_id')} is pending.")
                     flask.flash("Visitor entry pending. Waiting for Host approval.", 'warning')
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
                        time.sleep(2)
                    else:
                        flask.flash("Visitor entry logged successfully! (Host not found)", 'success')
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
        
    search = flask.request.args.get('search', None)
    status = flask.request.args.get('status', None)
    entries = get_all_entries(search, status)

    if flask.request.args.get('ajax'):
        return flask.render_template('partials/visitor_table_rows.html', entries=entries)

    return flask.render_template('view_all.html', entries=entries, search=search, visitor_status=status)

@app.route('/logistics')
def logistics():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    
    # Fetch recent vehicle entries
    recent_vehicles = vehicle_db.get_all_vehicles()
    recent_vehicles = recent_vehicles[:10] if recent_vehicles else []
    
    # Process dates for display (Same logic as logistics_exit)
    processed_vehicles = []
    if recent_vehicles:
        for v in recent_vehicles:
            v_safe = v.copy()
            raw_time = v.get('time')
            display_time = "Now"
            if raw_time:
                try:
                    parts = raw_time.replace('T', ' ').split(' ')
                    if len(parts) > 1:
                        time_part = parts[1]
                        display_time = time_part[:5]
                except:
                    display_time = str(raw_time)
            
            v_safe['display_time'] = display_time
            processed_vehicles.append(v_safe)
    
    return flask.render_template('logistics_entry.html', recent_vehicles=processed_vehicles)

@app.route('/logistics_exit')
def logistics_exit():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    
    try:
        # Fetch recent vehicle entries
        recent_vehicles = vehicle_db.get_all_vehicles()
        recent_vehicles = recent_vehicles[:10] if recent_vehicles else []

        # PRE-PROCESS DATA for template safety
        # This prevents Jinja2 runtime errors if 'time' or other fields are missing/malformed
        processed_vehicles = []
        for v in recent_vehicles:
            try:
                # Safe copy
                v_safe = v.copy()
                
                # Format time nicely in Python
                raw_time = v_safe.get('time')
                display_time = "Now"
                if raw_time:
                    try:
                        # Handle potential "T" separator or simple space
                        # clean ISO format: 2023-10-10T14:30:00 -> 14:30
                         # Split by T or space
                        parts = raw_time.replace('T', ' ').split(' ')
                        if len(parts) > 1:
                            # Take the time part HH:MM:SS
                            time_part = parts[1]
                            # Take just HH:MM
                            display_time = time_part[:5]
                    except:
                        display_time = str(raw_time) # Fallback
                
                v_safe['display_time'] = display_time
                processed_vehicles.append(v_safe)
            except Exception as e:
                logger.error(f"Error processing vehicle record for display: {e}")
                continue # Skip bad record

        return flask.render_template('logistics_exit.html', recent_vehicles=processed_vehicles)
        
    except Exception as e:
        logger.exception("CRITICAL ERROR in logistics_exit route")
        flask.flash("An internal error occurred while loading the page.", 'error')
        # Return a safe fallback or just the template with empty list to allow user to continue
        return flask.render_template('logistics_exit.html', recent_vehicles=[])

@app.route('/process_logistics_entry', methods=['POST'])
def process_logistics_entry():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))

    try:
        # 1. Handle File Upload
        photo_filename = None
        vehicle_img_local_path = None # Store local path for WhatsApp

        if 'vehicle_photo' in flask.request.files:
            file = flask.request.files['vehicle_photo']
            if file and file.filename != '':
                # Use persistent path next to the executable
                upload_folder = os.path.join(get_base_path(), 'uploads', 'vehicles')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Secure filename and save
                import time
                ext = os.path.splitext(file.filename)[1]
                timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
                safe_name = f"vehicle_{timestamp}{ext}"
                local_path = os.path.join(upload_folder, safe_name)
                
                # SAVE LOCALLY FIRST
                file.save(local_path)
                vehicle_img_local_path = local_path # Keep for WhatsApp
                
                # Default to local filename (Fallback)
                photo_filename = safe_name

                # --- Upload to Supabase ---
                try:
                    with open(local_path, 'rb') as f:
                        storage_path = f"vehicles/{safe_name}"
                        get_supabase_client().storage.from_("vehicles").upload(
                            file=f,
                            path=storage_path,
                            file_options={"content-type": file.content_type}
                        )
                        # Get Public URL
                        public_url = get_supabase_client().storage.from_("vehicles").get_public_url(storage_path)
                        # Remove query params if any
                        if "?" in public_url:
                             public_url = public_url.split("?")[0]
                        
                        logger.info(f"Uploaded to Supabase: {public_url}")
                        photo_filename = public_url # Success! Overwrite with URL
                except Exception as upload_err:
                    logger.error(f"Supabase Upload Failed (USING LOCAL FALLBACK): {upload_err}")
                    # photo_filename remains safe_name

        # 2. Extract Data
        data = {
            "driver_name": flask.request.form.get('driver_name'),
            "driver_phone": flask.request.form.get('driver_phone'),
            "veh_reg_no": flask.request.form.get('vehicle_number').upper(),
            "origin": flask.request.form.get('loc_from'),
            "destination": flask.request.form.get('loc_to'),
            "purchase_no": flask.request.form.get('purchase_number') or "N/A",
            "vehicle_img": photo_filename,
            "entry_type": "Entry",
            "tare_weight": flask.request.form.get('tare_weight'),
            "driver_id_type": flask.request.form.get('id_type'),
            "driver_id_number": flask.request.form.get('id_number'),
            "vehicle_length": flask.request.form.get('vehicle_length')
        }

        # 3. Insert into DB
        if vehicle_db.insert_vehicle(data):
            # 4. Send WhatsApp Notification (Async)
            try:
                def send_notification():
                    Logistics_message.send_whatsapp_message(
                        driver_name=data["driver_name"],
                        driver_phone=data["driver_phone"],
                        vehicle_number=data["veh_reg_no"],
                        from_location=data["origin"],
                        to_location=data["destination"],
                        vehicle_img_path=vehicle_img_local_path
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
        vehicle_img_local_path = None # Store local path for WhatsApp
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
                
                # Save locally FIRST
                local_path = os.path.join(upload_folder, safe_name)
                file.save(local_path)
                vehicle_img_local_path = local_path
                
                # Default to local filename (Fallback)
                photo_filename = safe_name

                # --- Upload to Supabase ---
                try:
                    with open(local_path, 'rb') as f:
                        
                        storage_path = f"vehicles/{safe_name}"
                        get_supabase_client().storage.from_("vehicles").upload(
                            file=f,
                            path=storage_path,
                            file_options={"content-type": file.content_type}
                        )
                        # Get Public URL
                        public_url = get_supabase_client().storage.from_("vehicles").get_public_url(storage_path)
                        # Remove query params if any
                        if "?" in public_url:
                             public_url = public_url.split("?")[0]
                        
                        logger.info(f"Uploaded to Supabase: {public_url}")
                        photo_filename = public_url # Use URL for DB
                except Exception as upload_err:
                    logger.error(f"Supabase Upload Failed (USING LOCAL FALLBACK): {upload_err}")
                    # photo_filename remains safe_name

        # 2. Extract Data
        data = {
            "driver_name": flask.request.form.get('driver_name'),
            "driver_phone": flask.request.form.get('driver_phone'),
            "veh_reg_no": flask.request.form.get('vehicle_number').upper(),
            "origin": flask.request.form.get('loc_from'),
            "destination": flask.request.form.get('loc_to'),
            "purchase_no": flask.request.form.get('purchase_number'),
            "is_returnable": 1 if flask.request.form.get('is_returnable') == '1' else 0,
            "material_type": flask.request.form.get('material_type'),
            "return_reason": flask.request.form.get('return_reason'),
            "vehicle_img": photo_filename,
            "entry_type": "Exit",
            "driver_id_type": flask.request.form.get('id_type'),
            "driver_id_number": flask.request.form.get('id_number')
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
                        vehicle_img_path=vehicle_img_local_path
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
    entry_type = flask.request.args.get('entry_type', None, type=str)
    
    # Fetch paginated vehicle entries
    result = vehicle_db.get_vehicles_paginated(page=page, per_page=per_page, search=search, entry_type=entry_type)
    
    return flask.render_template(
        'view_all_logistics.html', 
        vehicles=result.data,
        pagination=result,
        search=search or '',
        entry_type=entry_type or ''
    )

@app.route('/mark_returned/<int:vehicle_id>', methods=['POST'])
def mark_returned(vehicle_id):
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    if vehicle_db.mark_vehicle_returned(vehicle_id):
        flask.flash("Vehicle marked as returned successfully.", 'success')
    else:
        flask.flash("Failed to mark vehicle as returned. Error occurred.", 'error')
        
    # Redirect back to referring page or view_all_logistics
    return flask.redirect(flask.request.referrer or flask.url_for('view_all_logistics'))

@app.route('/check_out_page')
def check_out_page():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    
    search = flask.request.args.get('search', None)
    active_visitors = get_active_visitors(search)
    return flask.render_template('check_out.html', visitors=active_visitors, search=search)

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
    search = flask.request.args.get('search', '')
    role = flask.request.args.get('role', None)
    status = flask.request.args.get('status', None)
    employees = get_all_employees_full(search=search, role=role, status=status)
    return flask.render_template('view_status.html', employees=employees)

@app.route('/api/employees')
def api_employees():
    if not is_logged_in():
        return flask.jsonify({'error': 'Unauthorized'}), 401
    
    search = flask.request.args.get('search', None)
    role = flask.request.args.get('role', None)
    if role in ['All', '']:
        role = None
        
    status = flask.request.args.get('status', None)
    from employee_db import get_all_employees_full
    employees = get_all_employees_full(search=search, role=role, status=status)
    return flask.jsonify(employees)

# Check if this is the main entry point (mostly for development)
# For production/Waitress, this might be imported, so we should allow service start explicitly or on import
# But avoiding side effects on import is better. 
# We'll rely on the fact that app.py is often the entry point or we add a startup hook.

# Initialize WhatsApp Service
try:
    from whatsapp_service import whatsapp_service
    whatsapp_service.start()
except Exception as e:
    logger.error(f"Failed to start WhatsApp Service: {e}")

if __name__ == '__main__':
    # Ensure uploads directory exists
    os.makedirs(os.path.join(get_base_path(), 'uploads'), exist_ok=True)
    
    # Run the application
    # app.run(debug=True, host='0.0.0.0', port=5000)
    
    # Use Waitress for production-grade performance on Windows
    from waitress import serve
    print("Starting Waitress server on http://0.0.0.0:5000")
    serve(app, host='0.0.0.0', port=5000, threads=6)


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



@app.route('/api/pending_visitors')
def pending_visitors():
    if not is_logged_in():
        return flask.jsonify({'error': 'Unauthorized'}), 401
    
    host_name = flask.session.get('user')
    visitors = get_pending_visitors(host_name)
    return flask.jsonify(visitors)

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
        
    if action == 'forward':
        new_host = data.get('details') # 'details' holds the new host name for forward action
        from visitor_service import forward_visitor, get_visitor_by_id
        result = forward_visitor(visitor_id, new_host)
        status = 0 # Remains pending

        # [FIX] Send WhatsApp Notification if New Host is Offline
        if result['success']:
            try:
                # 1. Check New Host Status
                from employee_db import get_employee_by_name
                # get_employee_by_name expects a dict with 'name' key
                host_data = get_employee_by_name({"name": new_host})
                
                # If host is found and is OFFLINE (status 0)
                if host_data and host_data.get('status') == 0:
                     logger.info(f"Forwarded to Offline Host ({new_host}). Sending WhatsApp...")
                     
                     # 2. Get Visitor Details
                     visitor = get_visitor_by_id(visitor_id)
                     if visitor:
                         # 3. Send Message
                         from Whatsapp_message import send_message
                         
                         # Construct Message
                         msg_body = (
                             f"🚨 *New Visitor Forwarded*\n\n"
                             f"👤 *Visitor:* {visitor.get('name')}\n"
                             f"📞 *Phone:* {visitor.get('phone')}\n"
                             f"🏢 *Reason:* {visitor.get('reason')}\n"
                             f"📝 *Forwarded By:* {flask.session.get('user', 'Gate')}\n\n"
                             f"Please log in to the portal to approve/deny."
                         )
                         
                         host_phone = host_data.get('phone')
                         if host_phone:
                             threading.Thread(target=send_message, args=(host_phone, msg_body)).start()
                             logger.info("WhatsApp notification sent (Threaded).")
                         else:
                             logger.warning(f"Host {new_host} has no phone number.")
            except Exception as e:
                logger.error(f"Error sending forwarding notification: {e}")
    elif action == 'approve':
        status = 1
        result = update_visitor_status(visitor_id, status)
    elif action == 'deny':
        status = -1
        reason = data.get('reason')
        result = update_visitor_status(visitor_id, status, reason)
    else:
        return flask.jsonify({'success': False, 'error': 'Invalid action'})
    
    if result['success']:
        return flask.jsonify({'success': True, 'status': status})
    else:
        return flask.jsonify({'success': False, 'error': result['errors']})

@app.route('/sync_cache', methods=['POST'])
def sync_cache():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
    
    try:
        if sync_data_from_supabase(force=True):
            flask.flash("Employee cache synced successfully!", 'success')
        else:
            flask.flash("Failed to sync employee cache.", 'error')
    except Exception as e:
        logger.error(f"Error during manual cache sync: {e}")
        flask.flash("An error occurred during cache sync.", 'error')
        
    return flask.redirect(flask.url_for('home'))


# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring and container orchestration."""
    try:
        # Test database connectivity
        from db import get_db_connection
        conn = get_db_connection()
        # Perform a simple read to verify connection
        conn.table('visitors').select('id').limit(1).execute()
        
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
    
    # Initialize local cache
    init_cache()
    try:
        sync_data_from_supabase()
    except Exception as e:
        logger.error(f"Failed to sync data on startup: {e}")

    # Start the background sync thread
    sync_thread = threading.Thread(target=continuous_sync, daemon=True)
    sync_thread.start()
    logger.info("Continuous sync thread started from initialize_application.")


def continuous_sync():
    """Continuously sync data from Supabase in a background thread."""
    while True:
        try:
            logger.info("Starting periodic sync from Supabase...")
            sync_data_from_supabase(force=True)
            logger.info("Periodic sync finished.")
        except Exception as e:
            logger.error(f"Error in continuous sync thread: {e}")
        time.sleep(config_obj.SYNC_INTERVAL)


@app.route('/uploads/vehicles/<path:filename>')
def uploaded_vehicle_file(filename):
    upload_folder = os.path.join(get_base_path(), 'uploads', 'vehicles')
    return flask.send_from_directory(upload_folder, filename)

if __name__ == '__main__':
    
    # Initialize App Logic
    init_db()
    init_cache()
    
    # Initial sync from Supabase (must happen after init_cache creates tables)
    try:
        sync_data_from_supabase(force=True)
    except Exception as e:
        logger.error(f"Failed initial sync from Supabase: {e}")

    # Start the background sync thread
    sync_thread = threading.Thread(target=continuous_sync, daemon=True)
    sync_thread.start()

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