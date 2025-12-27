import flask
import threading
import time
from Whatsapp_message import send_message
from db import init_db
from visitor_service import save_visitor, get_all_entries
import os


app = flask.Flask(__name__)
app.secret_key = 'super_secret_key_for_demo' # Required for flash messages

# Initialize DB
init_db()

@app.route('/')
def home ():
    entries = get_all_entries() # For now, showing all. Could be recent.
    return flask.render_template('home.html', entries=entries)

@app.route('/data',methods=['GET','POST'])
def get_data():
    if flask.request.method == 'POST':
        name = flask.request.form['name']
        Number = flask.request.form['Number']
        host_number = flask.request.form['host_number']
        V_name = flask.request.form['V_name']
        reason = flask.request.form['reason']
        vehicle = flask.request.form.get('vehicle')
        vehicle_number = None
        if vehicle:
            vehicle_number = flask.request.form['vehicle_number']

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

@app.route('/entry_data',methods = ['GET','POST'])
def entry_data():
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
    return flask.render_template('view_all.html', entries=get_all_entries())   

if __name__ == '__main__':
    print("Starting Flask Server on port 5000...")
    app.run(debug=False, port=5000)

