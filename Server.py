import pulp
from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')



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
	x = 4 #solve() 
	return str(x)


if __name__ == '__main__':
	app.run(host='0.0.0.0') #debug=True
