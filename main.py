import argparse
import os
import shutil
import sys
import time

from lib.Utils import *
from lib.OsrmEngine import *
from lib.Agents import *
from lib.Demand import *
from lib.Constants import *
from lib.ModeChoice import *
from local import exe_loc, map_loc, use_singularity, simg_loc


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Agent-based model for Automated Mobility-on-Demand service simulation")
	parser.add_argument('-p', '--port', type=int, default=5000,
						help='Port number to use for OsrmEngine. Default 5000.')
	parser.add_argument('-f', '--fleet',
						help='Fleet sizes to simulate, formatted as comma-separated list (i.e. "-f 250,275,300")')
	parser.add_argument('-m', '--multiplier', type=float,
						help='Fare multiplier')
	parser.add_argument('-i', '--iteration', type=int,
						help='Iteration number (if running many in parallel parallel)')

	args = parser.parse_args()
	osrm_port = args.port

	if args.fleet:
		fleet_size_array = [int(x) for x in args.fleet.split(',')]
	else:
		fleet_size_array = FLEET_SIZE
	fare_multiplier = args.multiplier or 1.0

	if os.name != 'nt':
		map_destination = None
		# Sets separate maps directory for osrm to write processed maps to.
		# THIS WILL NOT WORK ON WINDOWS
		if args.iteration:
			map_destination = os.path.join(os.path.dirname(map_loc),
										   'osrm-maps-{}'.format(args.iteration))
			if not os.path.exists(map_destination):
				os.makedirs(map_destination)
			shutil.copy2(map_loc, map_destination)
			map_loc = os.path.join(map_destination, os.path.basename(map_loc))

	results_filename = './output/results{}{}{}.csv'.format(
		'-fleet'+str(args.fleet) if args.fleet else '',
		'-multi'+str(round(args.multiplier*100.)) if args.multiplier else '',
		'-iter'+str(args.iteration) if args.iteration else '')

	print('Writing results to {}'.format(results_filename))

	with open(results_filename, 'a') as results_file:
		writer = csv.writer(results_file)
		# row = ["ASC", "step", "ASSIGN", "REBL", "T_STUDY", "fleet_size", "capacity", "volume",
		# 	   "service_rate", "count_served", "count_reqs", "service_rate_ond", "count_served_ond",
		# 	   "count_reqs_ond", "service_rate_adv", "count_served_adv", "count_reqs_adv",
		# 	   "wait_time", "wait_time_adj", "wait_time_ond", "wait_time_adv", "in_veh_time", "detour_factor", 
		#  	   "veh_service_dist", "veh_service_time", "veh_service_time_percent", "veh_pickup_dist",
		#  	   "veh_pickup_time", "veh_pickup_time_percent", "veh_rebl_dist", "veh_rebl_time",
		#  	   "veh_rebl_time_percent", "veh_load_by_dist", "veh_load_by_time", "cost", "benefit", None]
		row = ["ASC", "step", "ASSIGN", "REBL", "T_STUDY", "fleet_size", "capacity", "volume", "service_rate",
			   "count_served", "count_reqs", "service_rate_ond", "count_served_ond", "count_reqs_ond", 
			   "service_rate_adv", "count_served_adv", "count_reqs_adv", "wait_time", "wait_time_adj",
			   "wait_time_ond", "wait_time_adv", "in_veh_time", "detour_factor", "veh_service_dist",
			   "veh_service_time", "veh_service_time_percent", "veh_pickup_dist", "veh_pickup_time",
			   "veh_pickup_time_percent", "veh_rebl_dist", "veh_rebl_time", "veh_rebl_time_percent",
			   "veh_load_by_dist", "veh_load_by_time", "cost", "benefit", "logsum_w_AVPT", "logsum_wout_AVPT",
			   "overall_logsum", "ridershipchange_car", "ridershipchange_walk", "ridershipchange_bike",
			   "ridershipchange_taxi", "ridershipchange_bus", "ridershipchange_rail", "ridershipchange_intermodal",
			   None]
		writer.writerow(row)

	# print(sys.argv)
	# if len(sys.argv) > 1:
	# 	for index in range(1:len(sys.argv):2):
	# 		try:
	# 			flag = sys.argv[index]
	# 			param = sys.argv[index+1]

	# 		except:
	# 			raise Exception("Invalid sysarg flags. See documentation for detail.")
	

	# if road network is enabled, initialize the routing server
	# otherwise, use Euclidean distance
	osrm = OsrmEngine(exe_loc, map_loc, use_singularity=use_singularity, simg_loc=simg_loc, gport=osrm_port)
	osrm.start_server()
	osrm.kill_server()
	osrm.start_server()
	osrm.kill_server()
	osrm.start_server()

	for fleet_size in fleet_size_array:
		veh_capacity = VEH_CAPACITY
		wait_time_adj = INI_WAIT
		detour_factor = INI_DETOUR
		demand_matrix = INI_MAT
		asc_avpt = ASC_AVPT
		counter = 0
		fare = []
		for counter, value in enumerate(FARE):
			if counter <= 2:
				p = value * fare_multiplier
				fare.append(p)
			else:
				p = value 
				fare.append(p)  
		# delete later
		print("fare:", fare)

		#initalize decision variables as 0 after each loop completion  
		df_OD_LOS = pd.DataFrame(pd.np.empty((1057, 6)) * pd.np.nan,columns=['m_id', 'summed_wait_time', 'summed_detour_factor', 'number_of_occurances','wait_time', 'detour_factor'])
		df_OD_LOS['m_id'] = df_OD_LOS.index
		df_OD_LOS['number_of_occurances'] = 0
		df_OD_LOS['summed_wait_time'] = 0
		df_OD_LOS['summed_detour_factor'] = 0
		df_OD_LOS['wait_time'] = int(INI_WAIT)
		df_OD_LOS['detour_factor'] = int(INI_DETOUR)

		#iteration
		for step in range(ITER_STEPS):
			# run simulation
			model, step, runtime, logsum_w_AVPT, logsum_wout_AVPT, df_diffprob = run_simulation(
				osrm, step, demand_matrix, fleet_size, veh_capacity, asc_avpt, fare, df_OD_LOS)
			# output the simulation results and save data
			wait_time_adj, detour_factor, df = print_results(
				model, step, runtime, fare, logsum_w_AVPT, logsum_wout_AVPT,fleet_size, fare_multiplier, df_diffprob, results_filename)
			df_OD_LOS = df.copy(deep=True)
		del df_OD_LOS

	if DIAGNOSTICS_ENABLED:
		lookup_stats_file = 'output/lookup-stats{}.txt'.format('-iter'+str(args.iteration) if args.iteration else '')
		osrm.print_lookup_stats(lookup_stats_file)

		key_stats_file = 'output/key-stats{}.txt'.format('-iter'+str(args.iteration) if args.iteration else '')
		found_keys_file = 'output/found-keys{}.csv'.format('-iter'+str(args.iteration) if args.iteration else '')
		unfound_keys_file = 'output/unfound-keys{}.csv'.format('-iter'+str(args.iteration) if args.iteration else '')
		osrm.print_key_stats(key_stats_file, found_keys_file, unfound_keys_file)