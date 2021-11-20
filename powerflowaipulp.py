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



def optimizer():
    print("Optimizing1!")

    systime = datetime.now()

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

    rate_divisor = 2
    charging_period = 5*rate_divisor #total time available for charging all vans (8pm-6am) [mins]
    simulation_time = charging_period + 2
    

    ## EVSE characteristics
    #manually input evse:
    #num_evse = 15 
    charging_rate = 10 #individual EVSE charging rate [kW]
        #L2: 7.7, 9.6, 11.5, 15.4, 19.2
        #L3: 25, 50, 100, 150, 200, 350

    # Van characteristics
    num_vans = 2 #total number of EVs that need to be charged during charging period
    battery_energy_capacity = 150  #battery energy capacity for the vans [kWh]
    soc_intial_min = 0.461
    soc_intial_mean= 0.666
    soc_intial_max= 0.865
    soc_final_min = 0.99 #minimum final battery state of charge (%)
    soc_final_max = 1.00 #final battery state of charge [%]
    battery_energy_initial_min = soc_intial_min * battery_energy_capacity #initial battery energy [kWh]
    battery_energy_initial_mean = soc_intial_mean * battery_energy_capacity #initial battery energy [kWh]
    battery_energy_initial_max = soc_intial_max * battery_energy_capacity #initial battery energy [kWh]
    battery_energy_final_min = 144#soc_final_min * battery_energy_capacity #final battery energy [kWh]
    battery_energy_final_max = 151#soc_final_max * battery_energy_capacity #final battery energy [kWh]
    print("Changed the energy final values because they should be in kw not % it seems, else it's the fidelity of the step up to charge that's causing infeasibility")

    battery_energy_initial = np.random.triangular(battery_energy_initial_min,
                                                battery_energy_initial_mean,
                                                battery_energy_initial_max,
                                                num_vans)

    #Estimate for amount of energy needed:
    expected_energy_amount = (battery_energy_final_min*num_vans)- sum(battery_energy_initial)
    expected_energy_cost = expected_energy_amount*(1/10*energy_rate_on+9/10*energy_rate_off)
    print(expected_energy_amount,expected_energy_cost)
    #calculate min evse:
    num_evse = int(math.ceil(expected_energy_amount/(charging_period/rate_divisor)/charging_rate))+2
    print("num_evse: ", num_evse)

    # Initialize lists to keep track of charging progress
    battery_energy_current = {} #current battery energy at time t [kWh]
    num_vans_charging_current = {} #number of vans charging concurrently at time t
    total_power_draw_current = {} #total power draw at time t [kW]
    energy_charge_at_time_t= {} #intitalize

    print(battery_energy_initial)

    ## =====================
    ## DECISION VARIABLES
    ## =====================

    charging_now = {} #binary: is van i charging at time t? 1 if van i is charging, 0 if not
    fully_charged = {} #binary: van i has been fully charged at time t
    peak = p.LpVariable('peak', lowBound = 0) #keep track of the peak over the charging period (using makespan)


    #charging_now = p.LpVariable.dicts(name="charging_now",
    #                 indexs=(range(num_vans), range(1, simulation_time)),#, range(M), range(L)),     
                     #lowBound=lower_bound_X,
                     #upBound=upper_bound_X,
    #                 cat=LpBinary)


    #fully_charged = p.LpVariable.dicts(name="fully_charged",
    #                 indexs=(range(num_vans), range(1, simulation_time)),# range(M), range(L)),     
                     #lowBound=lower_bound_X,
                     #upBound=upper_bound_X,
    #                 cat=LpBinary)

    print("We defined dicts @ ", datetime.now() - systime)


    for i in range(0, num_vans, 1):  #for each van i
        battery_energy_current[i, 0] = battery_energy_initial[i] #intialize
        charging_now[(i, 0)] = 0  #none are charging before charging period
        fully_charged[(i, 0)] = 0  #none are fully charged

        for t in range(1, simulation_time, 1):  #for each time t (hr)

            van_time_name = "van-" + str(i) + "-time-" + str(t)  # create a name for the decision variable
            charging_now[i, t] = p.LpVariable('van_time_name ' + str(i) +", "+ str(t),cat='Binary')  #binary: is van i charging at time t? 1 if van i is charging, 0 if not

            # Is charging for van i complete
            van_charge_complete_name = "van" + str(i) + "-charge_complete-" + str(t)  # create a name for the decision variable
            fully_charged[i, t] = p.LpVariable('van_charge_complete_name ' + str(i) +", "+ str(t),cat='Binary')  # 1 if charging is complete, 0 if not

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

        if t < 61:
            energy_charge_at_time_t[t] = energy_rate_on
        else:
            energy_charge_at_time_t[t] = energy_rate_off



        # Constraint: the total number of charging vans cannot exceed the total number of EV chargers on site at all times
        m += sum(charging_now[i, t] for i in range(0,num_vans,1)) <= num_evse
        # Constraint: the total power draw of vans charging cannot exceed the site transformer capacity
        m += sum((charging_now[i, t] * charging_rate) for i in range(0,num_vans,1)) <= site_power_capacity
        # Constraint: The peak makespan has to be bigger than the number of vans charging (aka
        m += peak >= sum((charging_now[i, t]*(charging_rate/rate_divisor)) for i in range(0, num_vans, 1))


    print("Next set of constraints @ ", datetime.now() - systime)

    # For all i constraints
    for i in range(0, num_vans, 1):  # For each van i
        for t in range(1, simulation_time, 1):  # for each time t

            #the battery energy increases by charging rate
            #Constraint: Dont exceed the max charge (aka battery capacity)
            m += battery_energy_current[i, 0]+sum(charging_now[i,t2]*(charging_rate/rate_divisor) for t2 in range(1,t+1)) <= battery_energy_final_max

            # Activation Constraints:
            # (Fully charged can only be 1 if charge is at least minimum threshold)
            m += fully_charged[i, t] <= (battery_energy_current[i, 0]+sum(charging_now[i,t2]*(charging_rate/rate_divisor) for t2 in range(1,t+1))) / battery_energy_final_min

            # fully_charged_at_t[i, t] >= (Charge[i, t] + charging_rate / 10) / max_charge – 1
            # m.addConstr(fully_charged[i, t] >= battery_energy_current[(i, t - 1)] / battery_energy_final_min + 0.00001 - 1)

            # Constraint: If you’re charging at time t-1, then you’re either charging at time t or you’re fully charged at time t
            m += charging_now[i, t - 1] <= charging_now[i, t] + fully_charged[i, t]

        # Constraint: All vehicles must be fully charged at the end of the simulation
        m += fully_charged[(i, simulation_time-1)] == 1

    ## =====================
    ## OBJECTIVE FUNCTION & RUNTIME
    ## =====================

    print("Set objective @ ", datetime.now() - systime)

    #set objective
    m += sum(sum((charging_now[i, t]*(charging_rate/rate_divisor)*energy_charge_at_time_t[t]) for i in range(0, num_vans, 1)) for t in range(1,simulation_time,1)) + peak*demand_rate


    #print(m)
    print('we made it to the solver @', datetime.now() - systime)
    print('The CPU usage is: ', psutil.cpu_percent(4))
    #
    print(p.listSolvers())
    status = m.solve(PULP_CBC_CMD(msg=1))#, p.COIN(maxSeconds=60*5)

    #status = p.solvers.actualSolve(m)
    print('The CPU usage is: ', psutil.cpu_percent(4))
    print(p.LpStatus[status])
    print('The CPU usage is: ', psutil.cpu_percent(4))
    print('Solver finished @', datetime.now() - systime)
    print("Peak demand rate: ",p.value(peak)*demand_rate)
    print(p.value(m.objective))
    return p.value(m.objective) 



optimizer()

if __name__ == "__optimizer__":

    print("Optimizing2!")



