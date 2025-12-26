import flask

app = flask.Flask(__name__)

entries = []

@app.route('/')
def home ():
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
        entries.append(entry)

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
    
if __name__ == '__main__':
    app.run(debug=True)