import flask
import threading
import time
from Whatsapp_message import send_message
from db import init_db
from visitor_service import save_visitor, get_all_entries, check_out_visitor, get_active_visitors
from employee_db import get_employee_phone, check_credentials, insert_employee
import os


app = flask.Flask(__name__)
app.secret_key = 'super_secret_key_for_demo' # Required for flash messages

# Initialize DB
init_db()

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
            flask.session['user'] = user['name']
            flask.session['auth_level'] = user['Auth_level'] # Store auth level
            return flask.redirect(flask.url_for('home'))

        # Fallback: Simple Hardcoded Credentials (ADMIN)
        if username == 'admin' and password == 'password123':
            flask.session['user'] = username
            flask.session['auth_level'] = 5 # Grant max authority to hardcoded admin
            return flask.redirect(flask.url_for('home'))
        else:
            flask.flash("Invalid credentials. Please try again.", 'error')
            
    return flask.render_template('login.html')

@app.route('/logout')
def logout():
    flask.session.pop('user', None)
    flask.session.pop('auth_level', None)
    return flask.redirect(flask.url_for('login'))

@app.route('/')
def index():
    return flask.redirect(flask.url_for('login'))

@app.route('/home')
def home ():
    if not is_logged_in():
        return flask.redirect(flask.url_for('login'))
        
    entries = get_all_entries() # For now, showing all. Could be recent.
    return flask.render_template('home.html', entries=entries)

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

            entry = {
                'name': name,
                'Number': Number,
                'V_name': V_name,
                'reason': reason,
                'vehicle': vehicle,
                'vehicle_number': vehicle_number
            }
            
            result = save_visitor(entry)
            if not result['success']:
                for error in result['errors']:
                    flask.flash(error, 'error')
                return flask.redirect(flask.url_for('home'))
                
            return flask.redirect(flask.url_for('entry_data',name=name,Number=Number,host_number=host_number,V_name=V_name,reason=reason,vehicle=vehicle,vehicle_number=vehicle_number))
            
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
        "name": name,
        "login_id": login_id,
        "phone": phone.replace("+91", "").strip(), # Clean it if user left +91
        "password": password,
        "Auth_level": auth_level
    }
    
    if insert_employee(data):
        flask.flash(f"User {name} added successfully!", 'success')
        return flask.redirect(flask.url_for('home'))
    else:
        flask.flash("Failed to add user. Login ID might be taken.", 'error')
        return flask.redirect(flask.url_for('new_user'))

if __name__ == '__main__':
    print("Starting Flask Server on port 5000...")
    app.run(host='0.0.0.0',debug=True, port=5000)

