import flask
import threading
app = flask.Flask(__name__)

from visitor_service import save_visitor, get_all_entries
from db import init_db
import os

app = flask.Flask(__name__)

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
            # Ideally flash error, but for now just print or ignore as per original simple flow
            print(result['errors'])
            
        return flask.redirect(flask.url_for('entry_data',name=name,Number=Number,V_name=V_name,reason=reason,vehicle=vehicle,vehicle_number=vehicle_number))

@app.route('/entry_data',methods = ['GET','POST'])
def entry_data():
    name = flask.request.args.get('name')
    Number = flask.request.args.get('Number')
    V_name = flask.request.args.get('V_name')
    reason = flask.request.args.get('reason')
    vehicle = flask.request.args.get('vehicle')
    vehicle_number = flask.request.args.get('vehicle_number')
    
    return flask.render_template('entry_data.html', name=name, Number=Number, V_name=V_name, reason=reason, vehicle=vehicle, vehicle_number=vehicle_number)
    time.sleep(5)
@app.route('/view_all')
def view_all():
    return flask.render_template('view_all.html', entries=get_all_entries())   

if __name__ == '__main__':
    app.run(debug=True)

