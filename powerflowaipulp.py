import pulp as p
import csv
import numpy as np
import xlsxwriter
import matplotlib.pyplot as plt
import math
from pulp import *

def optimizer():

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
    charging_period = 10*60 #total time available for charging all vans (8pm-6am) [mins]
    simulation_time = charging_period + 2

    ## EVSE characteristics
    #manually input evse:
    #num_evse = 15 
    charging_rate = 10 #individual EVSE charging rate [kW]
        #L2: 7.7, 9.6, 11.5, 15.4, 19.2
        #L3: 25, 50, 100, 150, 200, 350

    # Van characteristics
    num_vans = 25 #total number of EVs that need to be charged during charging period
    battery_energy_capacity = 150  #battery energy capacity for the vans [kWh]
    soc_intial_min = 0.461
    soc_intial_mean= 0.666
    soc_intial_max= 0.865
    soc_final_min = 0.99 #minimum final battery state of charge (%)
    soc_final_max = 1.00 #final battery state of charge [%]
    battery_energy_initial_min = soc_intial_min * battery_energy_capacity #initial battery energy [kWh]
    battery_energy_initial_mean = soc_intial_mean * battery_energy_capacity #initial battery energy [kWh]
    battery_energy_initial_max = soc_intial_max * battery_energy_capacity #initial battery energy [kWh]
    battery_energy_final_min = soc_final_min * battery_energy_capacity #final battery energy [kWh]
    battery_energy_final_max = soc_final_max * battery_energy_capacity #final battery energy [kWh]

    battery_energy_initial = np.random.triangular(battery_energy_initial_min,
                                                battery_energy_initial_mean,
                                                battery_energy_initial_max,
                                                num_vans)

    #Estimate for amount of energy needed:
    expected_energy_amount = (battery_energy_final_min*num_vans)- sum(battery_energy_initial)
    expected_energy_cost = expected_energy_amount*(1/10*energy_rate_on+9/10*energy_rate_off)
    print(expected_energy_amount,expected_energy_cost)
    #calculate min evse:
    num_evse = int(math.ceil(expected_energy_amount/(charging_period/60)/charging_rate))+2

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

    for i in range(0, num_vans, 1):  #for each van i
        battery_energy_current[i, 0] = battery_energy_initial[i] #intialize
        charging_now[(i, 0)] = 0  #none are charging before charging period
        fully_charged[(i, 0)] = 0  #none are fully charged

        for t in range(1, simulation_time, 1):  #for each time t (hr)

            van_time_name = "van-" + str(i) + "-time-" + str(t)  # create a name for the decision variable
            charging_now[(i, t)] = p.LpVariable('van_time_name',cat='Binary')  #binary: is van i charging at time t? 1 if van i is charging, 0 if not

            # Is charging for van i complete
            van_charge_complete_name = "van" + str(i) + "-charge_complete-" + str(t)  # create a name for the decision variable
            fully_charged[(i, t)] = p.LpVariable('van_charge_complete_name',cat='Binary')  # 1 if charging is complete, 0 if not

    ## =====================
    ## CONSTRAINTS
    ## =====================

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

        for i in range(0, num_vans, 1):  # For each van i
            num_vans_charging = num_vans_charging + charging_now[(i, t)]
            total_power_draw = total_power_draw + charging_now[(i, t)] * charging_rate

        # Constraint: the total number of charging vans cannot exceed the total number of EV chargers on site at all times
        m += num_vans_charging <= num_evse

        # Constraint: the total power draw of vans charging cannot exceed the site transformer capacity
        m += total_power_draw <= site_power_capacity

        # Terms for the peak makespan
        num_vans_charging_current[t] = num_vans_charging
        total_power_draw_current[t] = total_power_draw

        energy_cost = energy_cost + total_power_draw*(1/60)*energy_charge_at_time_t[t]

    # For all i constraints
    for i in range(0, num_vans, 1):  # For each van i
        for t in range(1, simulation_time, 1):  # for each time t

            #the battery energy increases by charging rate
            battery_energy_current[i, t] = battery_energy_current[i, t - 1] + charging_now[(i, t)] * (charging_rate/60)

            # Constraint: Dont exceed the max charge (aka battery capacity)
            m += battery_energy_current[i, t] <= battery_energy_final_max

            # Activation Constraints:
            # (Fully charged can only be 1 if charge is at least minimum threshold)
            m += fully_charged[(i, t)] <= battery_energy_current[(i, t - 1)] / battery_energy_final_min

            # fully_charged_at_t[i, t] >= (Charge[i, t] + charging_rate / 10) / max_charge – 1
        # m.addConstr(fully_charged[(i, t)] >= battery_energy_current[(i, t - 1)] / battery_energy_final_min + 0.00001 - 1)

            # Constraint: If you’re charging at time t-1, then you’re either charging at time t or you’re fully charged at time t
            m += charging_now[(i, t - 1)] <= charging_now[(i, t)] + fully_charged[(i, t)]

        # Constraint: All vehicles must be fully charged at the end of the simulation
        m += fully_charged[(i, t)] == 1

        
    for t in range(1, simulation_time - 1, 1):  # for each time t
        # Constraint: The peak makespan has to be bigger than the number of vans charging (aka
        m += peak >= total_power_draw_current[t]

        # want peak to occurr earlier the shift rather than later
        #m.addConstr(total_power_draw_current[t] >= total_power_draw_current[t+1]) #optinal constraint  for smoothness

    ## =====================
    ## OBJECTIVE FUNCTION & RUNTIME
    ## =====================

    total_electricity_cost = energy_cost + peak*demand_rate

    #Constraint: set a lower bound for the energy cost (warm start for faster runtime)
    m += total_electricity_cost >= expected_energy_cost
    #set objective
    m += total_electricity_cost
    #set runtime
    #m.Params.timeLimit = 60 * 1 #[mins]

    status = prob.solve()
    print(p.value(m.objective))

    ## =====================
    ## OUTPUT FILES
    ## =====================

    xlsx_title = "output-num_evse-"+str(num_evse)+"-num_vans-"+str(num_vans)+"-charging_time_limit-"+str(simulation_time-2)+".xlsx"

    # =================Fill the Matrix into Proper form for outputs

    # Van Charge Over Time
    van_charge_over_time = []
    time_range = ["van", *range(0, simulation_time, 1)]
    van_charge_over_time.append(time_range)
    for i in range(0, num_vans, 1):  # For each van i
        van_results = [i]  # Intialize with the van indicator
        van_results.append(battery_energy_current[i, 0])  # Append the intial state
        for t in range(2, simulation_time + 1, 1):  # for each time t
            new_charge = van_results[t - 1] + (charging_now[(i, t - 1)].x) * (charging_rate/60)
            van_results.append(new_charge)
        van_charge_over_time.append(van_results)

    # PowerDrawOverTime
    power_draw_over_time = []
    power_draw_over_time.append(time_range)
    for i in range(0, num_vans, 1):  # For each van i
        power_results = [i]  # Intialize with the van indicator
        power_results.append(0)  # Append the intial state
        for t in range(2, simulation_time + 1, 1):  # for each time t
            power_draw = (charging_now[(i, t - 1)].x) * charging_rate
            power_results.append(power_draw)
        power_draw_over_time.append(power_results)

    power_draw_sum = ['sum', 0]
    for t in range(2, simulation_time + 1, 1):  # for each time t
        col_sum = 0
        for i in range(0, num_vans, 1):  # For each van i
            col_sum = col_sum + (charging_now[(i, t - 1)].x) * charging_rate
        power_draw_sum.append(col_sum)
    power_draw_over_time.append(power_draw_sum)

    #Output to a file
    with xlsxwriter.Workbook(xlsx_title) as workbook:
        worksheet1 = workbook.add_worksheet('van_charge_over_time')

        for row_num, data in enumerate(van_charge_over_time):
            worksheet1.write_row(row_num, 0, data)

        worksheet2 = workbook.add_worksheet('power_draw_over_time')
        for row_num, data in enumerate(power_draw_over_time):
            worksheet2.write_row(row_num, 0, data)

        worksheet3 = workbook.add_worksheet('cost')
        cost=[[peak.x*demand_rate],[m.objVal-peak.x*demand_rate],[m.objVal]]
        print(cost)
        for row_num, data in enumerate(cost):
            worksheet3.write_row(row_num, 0, data)

    #Creating the relevant plots
    #Plot of power draw over time
    plt.figure()
    plt.plot(time_range[1:], power_draw_sum[1:])
    plt.xlim([1, simulation_time -2])
    plt.axes().set_xlabel("time (minutes)")
    plt.axes().set_ylabel(" Power (kW) ")
    plt.grid(which='major', axis='both')

    #Plot the individual van battery energy over time
    plt.figure()
    time_plot = [*range(0, simulation_time, 1)]
    counter = 0
    for row in van_charge_over_time:
        if counter >0:
            plt.plot(time_plot, row[1:], marker='o',label=str(counter-1))
        counter = counter +1
    plt.legend()
    plt.axes().set_xlabel("time (minutes)")
    plt.axes().set_ylabel(" Battery Energy (kWh) ")
    plt.grid(which='major', axis='both')
    plt.show()

    return p.value(m.objective) 

optimizer()


"""
# after optimizing, write to output file
with open('power_draw_over_tme.csv', mode='w', newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    for i in range(0, num_vans, 1):  # For each van i
        ans_list = [i] # first column is van id
        for t in range(1, simulation_time, 1):  # for each time t
            ans_list += [charging_now[(i, t)].x] #times charging rate
        # write row to file
        writer.writerow(ans_list)

# after optimizing, write to output file
with open('charging_complete_over_time.csv', mode='w', newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
    for i in range(0, num_vans, 1):  # For each van i
        ans_list2 = [i] # first column is van id
        for t in range(1, simulation_time, 1):  # for each time t
            ans_list2 += [fully_charged[(i, t)].x]
        # write row to file
        writer.writerow(ans_list2)


with open("out.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(ans)


"""
