import csv
import datetime
import os
import shelve
import sys
import time

sys.path.append('../')

from lib.OsrmEngine import *
from local import *


def main():
	os.chdir('../')

	osrm = OsrmEngine(exe_loc, map_loc, gport=5000)
	osrm.start_server()
	osrm.kill_server()
	osrm.start_server()

	locs = list()
	unique_ods_path = 'lib/ModeData/unique_ODs.csv'
	with open(unique_ods_path) as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			locs.append((row[0], row[1]))

	# locs = locs[1:10]

	# od_distances = {origin: dict() for origin in locs}
	# od_durations = {origin: dict() for origin in locs}
	# od_routings = {origin: dict() for origin in locs}

	shelf_files = {
		'distance': 'output/od-distances',
		'duration': 'output/od-durations',
		'routings': 'output/od-routings',
	}

	for key in shelf_files:
		s = shelve.open(shelf_files[key], flag='n')
		s.close()
	
	# outfiles = {
	# 	'distance': 'output/ODDistances.py',
	# 	'duration': 'output/ODDurations.py',
	# 	'routings': 'output/ODRoutings.py',
	# }

	# print('od_distances = {', file=open(outfiles['distance'], 'w+'), end='')
	# print('od_durations = {', file=open(outfiles['duration'], 'w+'), end='')
	# print('od_routings = {', file=open(outfiles['routings'], 'w+'), end='')

	start = time.time()
	total_iters = len(locs)

	for iteration, origin in enumerate(locs):
		print('Beginning computation for origin: {}'.format(origin))
		iterstarttime = time.time()
		
		origin_distances = {destination: 0 for destination in locs if destination != origin}
		origin_durations = {destination: 0 for destination in locs if destination != origin}
		origin_routings = {destination: dict() for destination in locs if destination != origin}

		# for key in outfiles:
			# print('{}: '.format(origin), file=open(outfiles[key], 'a+'), end='')

		for destination in locs:
			# print(destination)
			if destination != origin:
				distance, duration = osrm.get_distance_duration(origin[0], origin[1], destination[0], destination[1])
				origin_distances[destination] = distance
				origin_durations[destination] = duration

				routing = osrm.get_routing(origin[0], origin[1], destination[0], destination[1])

				steps = routing['steps']
				condensed_steps = list()

				for step in steps:
					c_step = dict()
					c_step['distance'] = step['distance']
					c_step['duration'] = step['duration']
					c_step['geometry'] = dict()
					c_step['geometry']['coordinates'] = step['geometry']['coordinates']

					condensed_steps.append(c_step)

				# print(condensed_steps)

				origin_routings[destination] = {'distance': routing['distance'],
												'duration': routing['duration'],
												'steps': condensed_steps}
			else:
				# print('Destination and origin are the same!')
				pass

		# print('{}, '.format(origin_distances), file=open(outfiles['distance'], 'a+'), end='')
		# print('{}, '.format(origin_durations), file=open(outfiles['duration'], 'a+'), end='')
		# print('{}, '.format(origin_routings), file=open(outfiles['routings'], 'a+'), end='')

		distance_shelf = shelve.open(shelf_files['distance'], flag='w')
		distance_shelf[repr(origin)] = origin_distances
		distance_shelf.close()

		duration_shelf = shelve.open(shelf_files['duration'], flag='w')
		duration_shelf[repr(origin)] = origin_durations
		duration_shelf.close()

		routings_shelf = shelve.open(shelf_files['routings'], flag='w')
		routings_shelf[repr(origin)] = origin_routings
		routings_shelf.close()

		iterendtime = time.time()
		print('Computation for origin complete...')
		print('Time elapsed: {}'.format(iterendtime - iterstarttime))
		proj_finish = datetime.datetime.fromtimestamp(start + ((total_iters / (iteration + 1)) * (iterendtime - start))).strftime('%c')
		print('Projected end time: {}'.format(proj_finish))

	# for key in outfiles:
		# print('}', file=open(outfiles[key], 'a+'), end='')

	# del origin_distances
	# del origin_durations
	# del origin_routings

	# from ODDistances import od_distances
	# pickle.dump(od_distances, open('od-distances.p', 'w+'))

	# from ODDurations import od_durations
	# pickle.dump(od_durations, open('od-durations.p', 'w+'))

	# from ODRoutings import od_routings
	# pickle.dump(od_routings, open('od-routings.p', 'w+'))

if __name__=='__main__':
	main()