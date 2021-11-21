import pulp
from flask import Flask, render_template, request, redirect
from flaskext.mysql import MySQL
from datetime import datetime
from datetime import timedelta
import pytz
import sys
from powerflowaipulp import *#optimizer
app = Flask(__name__)

#See this to kill: https://stackoverflow.com/questions/4465959/python-errno-98-address-already-in-use

# connect to db
#ToDo Connect to DB
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'admin' 
root_mysql_pass='a7dd542f856d82917597552e3531df962557c4169e225f36'
admin_pass = 'eb779ad7864c5b010441550bc3903c4bf73f58bd868ed52a'
app.config['MYSQL_DATABASE_PASSWORD'] = admin_pass
app.config['MYSQL_DATABASE_DB'] = 'Vehicles' 
app.config['MYSQL_DATABASE_HOST'] = 'localhost' #ToDo: Update from localhost?. IP? 142.93.179.86:22 or 127.0.0.1
#app.config['MYSQL_DATABASE_PORT'] = 3306
mysql.init_app(app)




@app.route('/')
def index():
	return render_template('index.html')




#ToDo: Create SQL Table, create HTML? See https://github.com/onexi/threetiers/blob/main/web/templates/index.html
#ToDo: Typecast all vars?
#ToDo: do type checking on form
@app.route('/addVehicle', methods = ['POST'])
def addVehicle():
	# Fetch form data
	vehicle = request.form
	addVehicleUnwrapped(vehicle)
	return render_template('/index.html') #ToDo: reroute to index.html instead? Note optimize is next step in workflow #return redirect('/GetVehicles')


def addVehicleUnwrapped(vehicle):
	vehicleNo = vehicle['vehicleNo']
	pytz.utc.localize( datetime.utcnow() )  
	currentTime =  str(datetime.now()-timedelta(hours=5))
	print(currentTime)
	currentCharge = vehicle['currentCharge']
	desiredCharge = vehicle['desiredCharge']
	departureTime = vehicle['departureTime']
	newStatus = vehicle['newStatus']

	update(vehicleNo)


	cur = mysql.get_db().cursor()
	cur.execute("INSERT INTO Vehicles(vehicleNo, currentTime, currentCharge, desiredCharge, departureTime, newStatus, recordStatus) VALUES(%s, %s, %s, %s, %s, %s, 'active')",(vehicleNo, currentTime, currentCharge, desiredCharge, departureTime, newStatus))
	mysql.get_db().commit()




def update(v):
    # Fetch form data
    id = v
    cur = mysql.get_db().cursor()
    cur.execute("UPDATE Vehicles SET recordStatus='inactive' WHERE vehicleNo=%s",(id))
    mysql.get_db().commit()
    return




#ToDo: Create HTML? See https://github.com/onexi/threetiers/blob/main/web/templates/colleges.html
#ToDo: Typecast all vars to str?
@app.route('/GetVehicles/')
def GetVehicles():
	d = getVehiclesUnwrapped()
	empty = {}
	if d != empty
		return render_template('GetVehicles.html', list=d) #render_template('GetVehicles.html', list=GetVehicles)
	




def getVehiclesUnwrapped():
	cursor = mysql.get_db().cursor()
	response = cursor.execute("SELECT * FROM Vehicles")
	html = ''
	print(response, file=sys.stderr)
	d = {}

	if response > 0:
		GetVehicles = cursor.fetchall()
		d = readVehicles(GetVehicles)

	return d




@app.route('/optimize/')
def optimize():
	res = optimizer(getVehiclesUnwrapped())
	show = 'Cost= ' + res[0]
	vehicles = res[1]
	for v in vehicles:
		addVehicleUnwrapped(vehicles[v])
		if vehicles[v]['pushDeparture']>0:
			show += ' ... warning, vehicle ' + v + ' has a new, delayed departure time...  '

	return str(show)


if __name__ == '__main__':
	app.run(host='0.0.0.0') #debug=True






