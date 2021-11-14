import pulp
from flask import Flask, render_template, request, redirect
from flaskext.mysql import MySQL
app = Flask(__name__)

#See this to kill: https://stackoverflow.com/questions/4465959/python-errno-98-address-already-in-use

# connect to db
#ToDo Connect to DB
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root' 
root_mysql_pass='a7dd542f856d82917597552e3531df962557c4169e225f36'
app.config['MYSQL_DATABASE_PASSWORD'] = root_mysql_pass
app.config['MYSQL_DATABASE_DB'] = 'Vehicles' 
app.config['MYSQL_DATABASE_HOST'] = '142.93.179.86' #ToDo: Update from localhost?. IP?
mysql.init_app(app)




@app.route('/')
def index():
	return render_template('index.html')

#ToDo: Create SQL Table, create HTML? See https://github.com/onexi/threetiers/blob/main/web/templates/index.html
#ToDo: Typecast all vars?
@app.route('/addVehicle', methods=['POST'])
def addVehicle():
    # Fetch form data
    vehicle = request.form
    vehicleNo = vehicle['vehicleNo']
    currentTime = vehicle['currentTime']
    currentCharge = vehicle['currentCharge']
    desiredCharge = vehicle['desiredCharge']
    departureTime = vehicle['departureTime']
    newStatus = vehicle['newStatus']

    cur = mysql.get_db().cursor()
    cur.execute("INSERT INTO Vehicles(vehicleNo, currentTime, currentCharge, desiredCharge, departureTime, newStatus) VALUES(%s, %s, %s, %s, %s, %s)",(vehicleNo, currentTime, currentCharge, desiredCharge, departureTime, newStatus))
    mysql.get_db().commit()
    return redirect('/GetVehicles') #ToDo: reroute to index.html instead? Note optimize is next step in workflow



#ToDo: Create HTML? See https://github.com/onexi/threetiers/blob/main/web/templates/colleges.html
#ToDo: Typecast all vars to str?
@app.route('/GetVehicles')
def GetVehicles():
    cursor = mysql.get_db().cursor()
    response = cursor.execute("SELECT * FROM Vehicles")
    html = ''    
    if response > 0:
        GetVehicles = cursor.fetchall()
        return render_template('GetVehicles.html', list=GetVehicles)




#ToDo: Replace with Pulp Version of Peter's optimization project code 
def solve():
	x = pulp.LpVariable("x", 0, 3)
	y = pulp.LpVariable("y", 0, 1)

	prob = pulp.LpProblem("myProblem", pulp.LpMinimize)

	prob+= x+y<=2
	prob+= -4*x + y

	status = prob.solve()

	print("RESULT:")

	print(pulp.LpStatus[status])

	print(pulp.value(x))
	print(-4*pulp.value(x) + pulp.value(y))
	return pulp.value(x)






@app.route('/optimize/')
def my_link():
	x = solve() 
	return str(x)


if __name__ == '__main__':
	app.run(host='0.0.0.0') #debug=True
