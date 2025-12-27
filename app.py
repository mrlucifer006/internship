import flask
import threading
import time
from Whatsapp_message import send_message
from db import init_db
from visitor_service import save_visitor, get_all_entries
from employee_db import get_employee_phone
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
        
        # Simple Hardcoded Credentials
        if username == 'admin' and password == 'password123':
            flask.session['user'] = username
            return flask.redirect(flask.url_for('home'))
        else:
            flask.flash("Invalid credentials. Please try again.", 'error')
            
    return flask.render_template('login.html')

@app.route('/logout')
def logout():
    flask.session.pop('user', None)
    return flask.redirect(flask.url_for('login'))

@app.route('/')
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

if __name__ == '__main__':
    print("Starting Flask Server on port 5000...")
    app.run(debug=True, port=5000)

