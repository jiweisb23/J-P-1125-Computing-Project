import pulp as p
import csv
import numpy as np
import xlsxwriter
import matplotlib.pyplot as plt
import math
from pulp import *
import psutil


from datetime import datetime
from datetime import timedelta
import pytz
import sys





#This function reads a text list that is output from the database and returns a dictionary of vehicles with their params
def readVehicles(db):
    vehicles = {}
    datefmt = '%Y-%m-%d %H:%M'
    for r in db:
        if r[8] == 'active':
            v = r[0]
            vehicles[v]={}
            dt = r[1].split(":")[0] + ':' + r[1].split(":")[1]
            vehicles[v]['vehicleNo'] = v
            vehicles[v]['currentTime'] = datetime.strptime(dt, datefmt )
            vehicles[v]['currentCharge'] = (float(r[2]))/100.
            vehicles[v]['desiredCharge'] = (float(r[3]))/100.
            dt = r[4].split(":")[0] + ':' + r[4].split(":")[1]
            vehicles[v]['departureTime'] = datetime.strptime(dt, datefmt)
            vehicles[v]['newStatus'] = r[5]
            vehicles[v]['lastChargingStatus'] = r[6]
            vehicles[v]['recommendedChargeTime'] = r[7]

    return vehicles


#These are fake dictionaries of vehicles used for testing
test_dict = {'2': {'currentTime': datetime(2021, 11, 21, 9, 0), 'currentCharge': .15, 'desiredCharge': .90, 'departureTime': datetime(2021, 11, 21, 13, 31), 'newStatus': 'Arrived', 'lastChargingStatus': None, 'recommendedChargeTime': None}, '1': {'currentTime': datetime(2021, 11, 21, 9, 1), 'currentCharge': .10, 'desiredCharge': .90, 'departureTime': datetime(2021, 11, 21, 17, 31), 'newStatus': 'Charging', 'lastChargingStatus': None, 'recommendedChargeTime': None}}
test_dict2 = {'3': {'vehicleNo': '3', 'currentTime': datetime(2021, 11, 25, 10, 52), 'currentCharge': .3456944444444444, 'desiredCharge': .900, 'departureTime': datetime(2021, 11, 26, 10, 0), 'newStatus': 'Arrived', 'lastChargingStatus': 'False', 'recommendedChargeTime': datetime(2021, 11, 26, 9, 14, 15, 504989), 'hoursToDeparture': 21.762222222222224, 'hoursCharging': 1.3708333333333333, 'battery_energy_current': 51.854166666666664, 'pushDeparture': 0}, '4': {'vehicleNo': '4', 'currentTime': datetime(2021, 11, 25, 11, 49), 'currentCharge': .300, 'desiredCharge': .950, 'departureTime': datetime(2021, 11, 25, 21, 59, 16), 'newStatus': 'Arrived', 'lastChargingStatus': 'False', 'recommendedChargeTime': datetime(2021, 11, 25, 12, 44, 15, 504989), 'hoursToDeparture': 4.762222222222222, 'hoursCharging': 0, 'battery_energy_current': 45.0, 'pushDeparture': 4.987777777777778}, '5': {'vehicleNo': '5', 'currentTime': datetime(2021, 11, 25, 12, 8), 'currentCharge': .300, 'desiredCharge': .800, 'departureTime': datetime(2021, 11, 25, 19, 44, 16), 'newStatus': 'Arrived', 'lastChargingStatus': 'False', 'recommendedChargeTime': datetime(2021, 11, 25, 12, 44, 15, 504989), 'hoursToDeparture': 3.762222222222222, 'hoursCharging': 0, 'battery_energy_current': 45.0, 'pushDeparture': 3.737777777777778}}
test_dict3 = {'2': {'currentTime': datetime(2021, 11, 29, 10, 30), 'currentCharge': .15, 'desiredCharge': .90, 'departureTime': datetime(2021, 11, 30, 13, 31), 'newStatus': 'Arrived', 'lastChargingStatus': None, 'recommendedChargeTime': None}}


#This function takes a dictionary of vehicles and current time and runs the optimization problem to provide a charging plan
def optimizer(vehicles, curTime):

    systime = datetime.now()

    #initialize the optimization problem
    m = p.LpProblem('Charging', p.LpMinimize)
    np.random.seed(2)

    ## ====================
    ## PARAMETERS
    ## ====================

    ## Initialize costs
    total_electricity_cost = 0  #total elecricity cost [$]
    energy_cost = 0 #cost for kWh [$]

    ## Utility rate structure #
    energy_rate_flat = 0.17 #energy charge for flat rate structure [$/kWh]
    energy_rate_on = 0.13 #on-peak energy charge for TOU rate structure [$/kWh]
    energy_rate_off = 0.08 #off-peak energy charge for TOU rate structure [$/kWh]
    demand_rate = 15 #utility demand charge [$/kW]

    ## Site characteristics 
    site_power_capacity = 100000  #the site power capacity [kW]
        #common: 45, 75, 112.5, 150, 225, 300, 500, 750, and 1,000 kVA


    # Van characteristics
    num_vans = len(vehicles) #total number of EVs that need to be charged during charging period
    battery_energy_capacity = 150  #battery energy capacity for the vans [kWh]
    battery_energy_current = {} #current battery energy at time t [kWh]

    ## EVSE characteristics
    charging_rate = 10 #individual EVSE charging rate [kW]
        #L2: 7.7, 9.6, 11.5, 15.4, 19.2
        #L3: 25, 50, 100, 150, 200, 350
    rate_divisor = 2


    expected_energy_amount = 0
    maxHours = 0
    
    for v in vehicles:
        #Find & Store how long we have until departure
        if  vehicles[v]['departureTime'] > curTime: 
            hoursToDeparture =   (vehicles[v]['departureTime'] - curTime).seconds/60/60
        else:
            hoursToDeparture = 0 
        vehicles[v]['hoursToDeparture'] = hoursToDeparture

        #Find & Store how much we've charged arleady, calculate starting point
        if vehicles[v]['lastChargingStatus'] =='True' or vehicles[v]['newStatus'] == 'Charging':
            vehicles[v]['hoursCharging'] = max((curTime - vehicles[v]['currentTime']).seconds/60/60,0)
        else:
            vehicles[v]['hoursCharging'] = 0
        battery_energy_current[v, 0] = min(battery_energy_capacity, vehicles[v]['currentCharge']*battery_energy_capacity + vehicles[v]['hoursCharging']*(charging_rate/rate_divisor))     #intialize
        vehicles[v]['battery_energy_current'] = battery_energy_current[v,0]

        #find out how much energy is needed
        vehicleEnergyNeeded = (vehicles[v]['desiredCharge'] )*battery_energy_capacity - battery_energy_current[v, 0]
        expected_energy_amount+= vehicleEnergyNeeded


        #find out how much time we actually need for all desired charges
        pushDeparture = max(vehicleEnergyNeeded / charging_rate - hoursToDeparture,0)
        vehicles[v]['pushDeparture'] = pushDeparture 
        maxHours = max(hoursToDeparture + pushDeparture, maxHours)



    charging_period = maxHours #total time available for charging all vehicles
    simulation_time = int(charging_period*rate_divisor)+1  + 2


    #Estimate for amount of energy needed:
    #expected_energy_amount = (battery_energy_capacity*num_vans)- sum(battery_energy_initial)
    expected_energy_cost = expected_energy_amount*(1/10*energy_rate_on+9/10*energy_rate_off)
    print('expected_energy_amount: ', expected_energy_amount)
    print('expected_energy_cost: ', expected_energy_cost)

    #calculate min evse and print other metrics to console:
    num_evse = int(math.ceil(expected_energy_amount/(charging_period/rate_divisor)/charging_rate))+2
    print("num_evse: ", num_evse)
    print('NumVans: ', num_vans)
    print('SimHrs: ',charging_period)

    # Initialize lists to keep track of charging progress
    num_vans_charging_current = {} #number of vans charging concurrently at time t
    total_power_draw_current = {} #total power draw at time t [kW]
    energy_charge_at_time_t= {} #intitalize


    ## =====================
    ## DECISION VARIABLES
    ## =====================

    charging_now = {} #binary: is van i charging at time t? 1 if van i is charging, 0 if not
    fully_charged = {} #binary: van i has been fully charged at time t
    peak = p.LpVariable('peak', lowBound = 0) #keep track of the peak over the charging period (using makespan)


    print("We defined dicts @ ", datetime.now() - systime)


    for v in vehicles:  #for each van
        #initialize the decision variables' starting points at time 0
        fully_charged[v, 0] = 0 + battery_energy_current[v, 0] == battery_energy_capacity
        charging_now[v, 0] = 0 + ((vehicles[v]['lastChargingStatus']=='True' or vehicles[v]['newStatus'] == 'Charging' ) and (battery_energy_current[v, 0] < battery_energy_capacity) )
        

        for t in range(1, simulation_time, 1):  #for each time t (hr)

            #Create the decision variables
            van_time_name = "van-" + str(v) + "-time-" + str(t)  # create a name for the decision variable
            charging_now[v, t] = p.LpVariable('van_time_name ' + str(v) +", "+ str(t),cat='Binary')  #binary: is van i charging at time t? 1 if van i is charging, 0 if not

            # Is charging for van i complete
            van_charge_complete_name = "van" + str(v) + "-charge_complete-" + str(t)  # create a name for the decision variable
            fully_charged[v, t] = p.LpVariable('van_charge_complete_name ' + str(v) +", "+ str(t),cat='Binary')  # 1 if charging is complete, 0 if not

    ## =====================
    ## CONSTRAINTS
    ## =====================

    print("Begin Constraints @ ", datetime.now() - systime)

    energy_charge_at_time_t[0]=0
    # For all t constraints

    for t in range(1, simulation_time, 1):  # for each time t
        num_vans_charging = 0  # intialize the number of vans charging to be zero
        total_power_draw = 0  # intialize total power draw to be zero, this variable isnt used but would if we go to piecewise
        num_vans_charging_current[0] = 0

        #Calculate Energy rates during on peak and off peak times
        if t < 61:
            energy_charge_at_time_t[t] = energy_rate_on
        else:
            energy_charge_at_time_t[t] = energy_rate_off
       

        # Constraint: the total number of charging vans cannot exceed the total number of EV chargers on site at all times
        m += sum(charging_now[v, t] for i in range(0,num_vans,1)) <= num_evse
        # Constraint: the total power draw of vans charging cannot exceed the site transformer capacity
        m += sum((charging_now[v, t] * charging_rate) for v in vehicles) <= site_power_capacity
        # Constraint: The peak makespan has to be bigger than the number of vans charging (aka
        m += peak >= sum((charging_now[v, t]*(charging_rate/rate_divisor)) for v in vehicles)


    print("Next set of constraints @ ", datetime.now() - systime)

    # For all i constraints
    for v in vehicles:  # For each van i
        for t in range(1, simulation_time, 1):  # for each time t

            #the battery energy increases by charging rate
            #Constraint: Dont exceed the max charge (aka battery capacity)
            #Note a little buffer is included so we can exceed by a partial last time period
            m += battery_energy_current[v, 0]+sum(charging_now[v,t2]*(charging_rate/rate_divisor) for t2 in range(1,t+1)) <= 1 * battery_energy_capacity + charging_rate/rate_divisor - 1 

            # Activation Constraints:
            # (Fully charged can only be 1 if charge is at least minimum threshold)
            m += fully_charged[v, t] <= (battery_energy_current[v, 0]+sum(charging_now[v,t2]*(charging_rate/rate_divisor) for t2 in range(1,t+1))) / (vehicles[v]['desiredCharge'] * battery_energy_capacity ) #- charging_rate/rate_divisor+1 

            # fully_charged_at_t[i, t] >= (Charge[i, t] + charging_rate / 10) / max_charge – 1
            # m.addConstr(fully_charged[i, t] >= battery_energy_current[(i, t - 1)] / battery_energy_final_min + 0.00001 - 1)

            # Constraint: If you’re charging at time t-1, then you’re either charging at time t or you’re fully charged at time t
            m += charging_now[v, t - 1] <= charging_now[v, t] + fully_charged[v, t]

            

            if t >= (vehicles[v]['hoursToDeparture']+vehicles[v]['pushDeparture'])*rate_divisor+1:
                #Constraint: Can't charge after desired Departure time (end of period):
                m+= charging_now[v,t]==0
                # Constraint: All vehicles must be desired charged at the end of the simulation
                m+= fully_charged[v,t]==1

        

    ## =====================
    ## OBJECTIVE FUNCTION & RUNTIME
    ## =====================

    print("Set objective @ ", datetime.now() - systime)

    #set objective
    m += sum(sum((charging_now[v, t]*(charging_rate/rate_divisor)*energy_charge_at_time_t[t]) for v in vehicles) for t in range(1,simulation_time,1)) + peak*demand_rate


    #print(m)
    print('we made it to the solver @', datetime.now() - systime)
    print('The CPU usage is: ', psutil.cpu_percent(4))
    #

    #ToDo: Warm Start: https://coin-or.github.io/pulp/guides/how_to_mip_start.html
    status = m.solve(PULP_CBC_CMD(msg=1))#, p.COIN(maxSeconds=60*5)
    #Debugging: https://coin-or.github.io/pulp/guides/how_to_debug.html


    print('Solver finished @', datetime.now() - systime)
    print('The CPU usage is: ', psutil.cpu_percent(4))

    print(p.LpStatus[status], ": ", p.value(m.objective), " ... Peak Demand Rate: ", p.value(peak)*demand_rate)
    defaultCost = calcDefault(vehicles, energy_charge_at_time_t, demand_rate, battery_energy_capacity, simulation_time, charging_rate, rate_divisor)
    
    res = parseVehicleResult(vehicles, charging_now, rate_divisor, simulation_time, battery_energy_capacity, curTime)

    if p.LpStatus[status] != "Optimal":
        return ("NOT OPTIMAL", res)
    else:
        return (p.value(m.objective), res, defaultCost - p.value(m.objective)) 


#This function works with the optimizer to calculate the default savings if we just charged all vehicles from the start of the optimization
def calcDefault(vehicles, energy_charge_at_time_t, demand_rate, battery_energy_capacity, simulation_time, charging_rate, rate_divisor):
    defaultPeak = 0 #This variable will track the default value for the peak
    defaultCharge = 0 #This variable will track the default value for the total charge cost

    for t in range(1, simulation_time, 1):  # for each time t
        tempPeak = 0
        for v in vehicles:  # For each van i
            #If the van hasn't finished charging yet from the start of the run, keep charging it
            if t <= (vehicles[v]['desiredCharge']*battery_energy_capacity-vehicles[v]['battery_energy_current']+ charging_rate/rate_divisor - 1) / (charging_rate / rate_divisor):
                tempPeak += (charging_rate/rate_divisor)
                defaultCharge += (charging_rate/rate_divisor)*energy_charge_at_time_t[t]
        defaultPeak = max(tempPeak, defaultPeak)

    return defaultPeak*demand_rate + defaultCharge
        


#Given a dictionary of vehicles, this function will calculate the time of the beginning charging period and other important metrics to add to the dictionary and return it
def parseVehicleResult(vehicles, charging_now, rate_divisor, simulation_time, battery_energy_capacity, curTime):
    for v in vehicles:
        min_t = simulation_time
        for t in range(1, simulation_time, 1): 
            if p.value(charging_now[v, t]) == 1:
                min_t = min(min_t, t) #min_t will store the minimum time period in which the vehicle is charging

        vehicles[v]['recommendedChargeTime'] = (curTime) + timedelta(hours = (min_t-1)/rate_divisor )
        vehicles[v]['currentCharge'] = vehicles[v]['battery_energy_current'] / battery_energy_capacity * 100 #update the current charge as the starting point of the optimizer
        vehicles[v]['desiredCharge'] = vehicles[v]['desiredCharge'] * 100 #convert decimals back to percentage values
        vehicles[v]['departureTime'] = vehicles[v]['departureTime'] + timedelta(hours = vehicles[v]['pushDeparture']) #delay the departure time
        vehicles[v]['lastChargingStatus'] = str(min_t<=1)  #if charging now, change last charging status to true
    return vehicles


    


#print(optimizer(test_dict3, datetime.now()))

if __name__ == "__optimizer__":

    print("Optimizing2!")



