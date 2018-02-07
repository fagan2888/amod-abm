import time

from lib.Utils import *
from lib.OsrmEngine import *
from lib.Agents import *
from lib.Demand import *
from lib.Constants import *
from lib.ModeChoice import *
from local import exe_loc, map_loc


if __name__ == "__main__":
	# if road network is enabled, initialize the routing server
	# otherwise, use Euclidean distance
	osrm = OsrmEngine(exe_loc, map_loc)
	osrm.start_server()

	with open('output/results.csv', 'a', newline='') as f:
		writer = csv.writer(f)
		row = ["ASC", "step", "ASSIGN", "REBL", "T_STUDY", "fleet_size", "capacity", "volume",
		 "service_rate", "count_served", "count_reqs", "service_rate_ond", "count_served_ond", "count_reqs_ond", "service_rate_adv", "count_served_adv", "count_reqs_adv",
		 "wait_time", "wait_time_adj", "wait_time_ond", "wait_time_adv", "in_veh_time", "detour_factor", 
		 "veh_service_dist", "veh_service_time", "veh_service_time_percent", "veh_pickup_dist", "veh_pickup_time", "veh_pickup_time_percent",
		 "veh_rebl_dist", "veh_rebl_time", "veh_rebl_time_percent", "veh_load_by_dist", "veh_load_by_time", 
		 "cost", "benefit", None]
		writer.writerow(row)

	for fleet_size in FLEET_SIZE:
		veh_capacity = VEH_CAPACITY
		wait_time_adj = INI_WAIT
		detour_factor = INI_DETOUR
		demand_matrix = INI_MAT
		asc_avpt = ASC_AVPT # If UNCERTAIN=True, this will be overridden
		asc_name = ASC_NAME # If UNCERTAIN=True, this will be overridden
		uncertain = UNCERTAIN
	
		if uncertain:
			uncertain_params = generate_uncertainty()
			asc_avpt = uncertain_params['ASC_AVPT']
			asc_name = 'AVPT{}'.format(asc_avpt)
			beta_avpt_car_tt = uncertain_params['BETA_AVPT_CAR_TT']

		#iteration
		for step in range(ITER_STEPS):
			# run simulation
			model, step, runtime = run_simulation(osrm, step, demand_matrix, fleet_size, veh_capacity, asc_avpt, beta_avpt_car_tt, wait_time_adj, detour_factor)
			# output the simulation results and save data
			wait_time_adj, detour_factor = print_results(model, step, runtime, asc_name)