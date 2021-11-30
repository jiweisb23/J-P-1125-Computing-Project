import pulp
from flask import Flask, render_template, request, redirect
from flaskext.mysql import MySQL
from datetime import datetime
from datetime import timedelta
import pytz
import sys
from powerflowaipulp import *#optimizer
import jinja2
import os
app = Flask(__name__, static_url_path = '/static')


#See this to kill: https://stackoverflow.com/questions/4465959/python-errno-98-address-already-in-use

# connect to db
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'admin' 
root_mysql_pass='a7dd542f856d82917597552e3531df962557c4169e225f36'
admin_pass = 'eb779ad7864c5b010441550bc3903c4bf73f58bd868ed52a'
app.config['MYSQL_DATABASE_PASSWORD'] = admin_pass
app.config['MYSQL_DATABASE_DB'] = 'Vehicles' 
app.config['MYSQL_DATABASE_HOST'] = 'localhost' 
#app.config['MYSQL_DATABASE_PORT'] = 3306
mysql.init_app(app)




@app.route('/')
def index():
	return render_template('index.html')



@app.route('/about')
def about():
	return render_template('about.html')


#Add vehicle route adds a vehicle to the database
#but calls funciton addVehicleUnwrapped to do most of the work
@app.route('/addVehicle', methods = ['POST'])
def addVehicle():
	# Fetch form data
	vehicle = request.form
	addVehicleUnwrapped(vehicle, True)
	return render_template('/index.html') 


#This function is given manual inputs for a vehicle, and it inserts it into the database
def addVehicleUnwrapped(vehicle, fromHTML):
	vehicleNo = vehicle['vehicleNo']
	pytz.utc.localize( datetime.utcnow() )  
	currentTime =  str(datetime.now()-timedelta(hours=5))
	print(currentTime)
	currentCharge = vehicle['currentCharge']
	desiredCharge = vehicle['desiredCharge']
	departureTime = vehicle['departureTime']
	newStatus = vehicle['newStatus']

#The update function is called before the insert query to mark previous versions of this vehicle inactive
	update(vehicleNo)

#If from HTML page, we won't know the recommended charge time or status, but otherwise it's from the optimizer and thus we do 
	if fromHTML:
		cur = mysql.get_db().cursor()
		cur.execute("INSERT INTO Vehicles(vehicleNo, currentTime, currentCharge, desiredCharge, departureTime, newStatus, recordStatus) VALUES(%s, %s, %s, %s, %s, %s, 'active')",(vehicleNo, currentTime, currentCharge, desiredCharge, departureTime, newStatus))
		mysql.get_db().commit()


	else:
		lastChargingStatus = vehicle['lastChargingStatus']
		recommendedChargeTime = vehicle['recommendedChargeTime']
		cur = mysql.get_db().cursor()
		cur.execute("INSERT INTO Vehicles(vehicleNo, currentTime, currentCharge, desiredCharge, departureTime, newStatus, lastChargingStatus, recommendedChargeTime, recordStatus) VALUES(%s, %s, %s, %s, %s, %s,%s, %s, 'active')",(vehicleNo, currentTime, currentCharge, desiredCharge, departureTime, newStatus, lastChargingStatus, recommendedChargeTime))
		mysql.get_db().commit()

	






#The update function is given a vehicle id, and marks all instances of that vehicle in the database as inactive
def update(v):
    # Fetch form data
    id = v
    cur = mysql.get_db().cursor()
    cur.execute("UPDATE Vehicles SET recordStatus='inactive' WHERE vehicleNo=%s",(id))
    mysql.get_db().commit()
    return




#The getVehicles route is set up to call the getVehiclesUnwrapped function and return the results to the GetVehicles.html template
@app.route('/GetVehicles.html')
def GetVehicles():
	d = getVehiclesUnwrapped()
	if d != {}:
		return render_template('GetVehicles.html', dict=d) #render_template('GetVehicles.html', list=GetVehicles)
	



#The getVehiclesUnwrapped function queries the database for all active vehicles and sends the response to the readvehicles function 
def getVehiclesUnwrapped():
	cursor = mysql.get_db().cursor()
	response = cursor.execute("SELECT * FROM Vehicles WHERE recordStatus=%s", ('active'))
	html = ''
	print(response, file=sys.stderr)
	d = {}

	if response > 0:
		GetVehicles = cursor.fetchall()
		d = readVehicles(GetVehicles)

	return d


#The removePastDept function is given a current time and sets all vehicles which are departing before that time as inactive
def removePastDept(curTime):
    cur = mysql.get_db().cursor()
    cur.execute("UPDATE Vehicles SET recordStatus='inactive' WHERE departureTime<%s",(curTime))
    mysql.get_db().commit()
    return



#The optimize function performs all necessary optimization steps
@app.route('/optimize/')
def optimize():
	pytz.utc.localize( datetime.utcnow() ) 
	curTime = datetime.now()-timedelta(hours=5)
	removePastDept(curTime)

	#with current time inhand, get the active vehicles and send the results to the optimizer
	res = optimizer(getVehiclesUnwrapped(), curTime)

	#parse the results of the optimizer into costs, savings, and vehicles
	show = 'Cost = $' + str(round(res[0],2 ))
	show +="\n Savings = $" +str(round(res[2],2))
	vehicles = res[1]
	#print('len vehicles: ' + str(len(vehicles)))

	#if the result is not optimal, provide that message to the user. Else, show the results and update the database
	if res[0]=="NOT OPTIMAL":
		show = " ... Non-Optimal result, sorry! Database not updated" 
	else:
		for v in vehicles:
			print(v)
			addVehicleUnwrapped(vehicles[v], False)
			if vehicles[v]['pushDeparture']>0:
				show += '\n Warning, the departure time for vehicle ' + v + ' has been delayed by ' + str(round(vehicles[v]['pushDeparture']*60,1)) +' minutes'

	return str(show)


if __name__ == '__main__':
	app.run(host='0.0.0.0') #debug=True






