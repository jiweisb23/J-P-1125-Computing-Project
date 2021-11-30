# J-P-1125-Computing-Project

These are the final project files for the *1.125 Architecting & Engineering Software Systems* class at MIT.
Term: Fall 2021
Peter Jacobson & Josh Weisberg

## PowerFlow AI Online Optimizer

PowerFlow AI provides a suite of software solutions to simplify fleet electirification.
We ensure fleet operators charge their electric vehicles on time for departure while saving money.
Through the PowerFlow AI Dashboard, add vehicles as they arrive to the depot and then optimize the charging schedule to lower energy costs.

## How to Run the Optimizer

1. Log in to the Digital Ocean server through your local terminal, at IP address 142.93.179.86
2. Navigate to the following directory under the root folder: J-P-1125-Computing-Project/
3. Run the python server with the following command: python3 Server.py
4. Navigate to the webpage at IP address 142.93.179.86

## How the Optimizer Works

The PowerFlow AI website has two webpages, Dashboard and About. Navigage to each through the links on the top right corner of the webpage.

### About

Navigate here to learn more about PowerFlow AI.

### Dashboard

Navigate here to use the PowerFlow AI Optimizer. The Optimizer calculates the best charging schedule to minimize electricity costs while ensuring vehicles depart on time. The tool tells the user when to plug in each vehicle.

#### Add Vehicles

The Optimizer allows a user to add vehicles to it's database as they arrive to the depot or update vehicles in its database when vehicles are plugged in for charging. The form asks for the following:
1. Vehicle # [enter the vehicle idnetifier]
2. currentCharge [enter the current battery state of charge of the vehicle, 0-100%]
3. desiredCharge [enter the desired battery state of charge of the vehicle before it departs, 0-100%]
4. Departure Time (YYYY-MM-DD HH:MM) [enter the desired departure time of the vehicle]
5. NewStatus {Arrived / Charging}? [select Arrived for a newly arrived vehicle, select Charging for a vehicle that has been plugged in]

Once you click the Submit button, the a new vehicle will be added to the database or a vehicle in the database will have an updated charging status.

This tool can also be used for planning purposes.

#### Show Vehicles

Click the Show Vehicles button to open a new page that lists the active database. This database shows which vehicles are charging and at what time each vehicle should be plugged in (once optimized).

#### Optimize

Click the Optimize button to run the optimization algorithm to determine the best charging schedule for the current database of vehicles.

Please be patient, as results will show on the same page once the algorithm finishes its analysis.

## Packages and Resources

flask (python module for web application development)

pulp (linear programming modeler written in python, instructions here: https://pypi.org/project/PuLP/)

mysql (database management system)

datetime (module for date and time manipulation)

timedelta (use to determine time differences)

pytz (timezone calculation)

sys (system paramater library)

jinja2 (templating)

os (creating and removing directories)

csv (parse csv data in python)

numpy (library to handle arrays and matrices)

xlsxwriter (write to csv files)

matplotlib.pyplot (visulaizations in python)

math (define math functions)

psutil (access system details)

bootstrap (css templates)

Thank you to the LGO summer team for help on the charging algorithm.
