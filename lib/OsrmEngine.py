"""
Open Source Routing Machine (OSRM)
"""

import csv
import os
import requests
import json
import time
import math
import numpy as np
from subprocess import Popen, PIPE

from lib.Constants import *
from lib.LinkTravelTimes import link_travel_times_prec4 as LINK_TRAFFIC_DICT
from local import hostport, osrm_version


class OsrmEngine(object):
    """
    OsrmEngine is the class for the routing server
    Attributes:
        exe_loc: path of the routing server (osrm-routed executable) (irrelevant if using singularity)
        map_loc: path of the road network file (if using singularity, path of the .osm.pbf file)
        use_singularity: true if using singularity to access osrm-backend image
        simg_loc: path of the singularity image file
        ghost: host ip address
        gport: host port
        cst_speed: constant vehicle speed when road network is disabled (in meters/second
    """
    def __init__(self,
                 exe_loc,
                 map_loc,
                 use_singularity=False,
                 simg_loc=None,
                 ghost = hostport,
                 gport = 5000,
                 cst_speed = CST_SPEED):
        if not use_singularity and not os.path.isfile(exe_loc):
            raise Exception("Could not find the routing server at %s" % exe_loc)
        else:
            self.exe_loc = exe_loc

        if not os.path.isfile(map_loc):
            raise Exception("Could not find osrm road network data at %s" % map_loc)
        else:
            self.map_loc = map_loc

        if use_singularity and simg_loc is None:
            raise Exception("If using singularity, image to osrm-backend singularity image must be provided")
        elif use_singularity and not os.path.isfile(simg_loc):
            raise Exception("Could not find osrm-backend singularity image at %s" % simg_loc)
        else:
            self.use_singularity = use_singularity
            self.simg_loc = simg_loc

        self.ghost = ghost
        self.gport = gport
        self.cst_speed = cst_speed
        # remove any open instance
        if self.check_server():
            self.kill_server()

        # Generate the needed map files using OSRM backend if running in Singularity environment
        if self.use_singularity:
            # Use the specified map destination if there is any, otherwise just use the same dir as the base map
            map_directory = os.path.dirname(self.map_loc)
            map_basename = os.path.basename(self.map_loc).split('.')[0]

            from spython.main import Client
            Client.execute(self.simg_loc, ['osrm-extract','-p','/opt/car.lua',self.map_loc])

            self.osrm_map = os.path.join(map_directory, (map_basename + '.osrm'))
            if not os.path.isfile(self.osrm_map):
                raise Exception("%s failed to create during osrm-extract" % self.osrm_map)
            
            Client.execute(self.simg_loc, ['osrm-partition', self.osrm_map])
            Client.execute(self.simg_loc, ['osrm-customize', self.osrm_map])
            Client.execute(self.simg_loc, ['osrm-contract', self.osrm_map])

        global DISTANCE_USES_LOOKUP, DURATION_USES_LOOKUP, DISTDRTN_USES_LOOKUP, DISTANCE_USES_ENGINE, DURATION_USES_ENGINE, DISTDRTN_USES_ENGINE, ROUTING_COULD_LOOKUP, ROUTING_USES_ENGINE, FOUND_KEYS_DICT, UNFOUND_KEYS_DICT

        DISTANCE_USES_LOOKUP = 0
        DURATION_USES_LOOKUP = 0
        DISTDRTN_USES_LOOKUP = 0
        DISTANCE_USES_ENGINE = 0
        DURATION_USES_ENGINE = 0
        DISTDRTN_USES_ENGINE = 0
        ROUTING_COULD_LOOKUP = 0
        ROUTING_USES_ENGINE = 0
        FOUND_KEYS_DICT = dict()
        UNFOUND_KEYS_DICT = dict()

    # kill any routing server currently running before starting something new
    def kill_server(self):
        if self.use_singularity:
            print("Attempting to kill process %s" % self.process)
            counter = 0
            while self.process.is_alive() and counter<10:
                self.process.terminate()
                time.sleep(1)
                counter += 1
            print("Process is alive: %s" % self.process.is_alive())
        elif os.name == 'nt':
            # os.kill(self.pid, 1) # Kill process on windows
            os.system("taskkill /f /im osrm-routed.exe") # Kill process on windows
        else:
            Popen(["killall", os.path.basename(self.exe_loc)], stdin=PIPE, stdout=PIPE, stderr=PIPE) # Kill process on Mac/Unix
        time.sleep(2)
        self.process = None
        self.pid = None
        print( "The routing server \"http://%s:%d\" is killed" % (self.ghost, self.gport) )
        
    # check if server is already running
    def check_server(self):
        try:
             if requests.get("http://%s:%d" % (self.ghost, self.gport)).status_code == 400:
                return True
        except requests.ConnectionError:
            return False
    
    # start the routing server
    def start_server(self):
        if self.use_singularity: # Run a dedicated thread for the singularity backend since we cannot Popen

            import multiprocessing
            from spython.main import Client

            def run_simg_server(simg_loc, osrm_map):
                Client.execute(simg_loc, ['osrm-routed','--algorithm','mld','-p',str(self.gport), osrm_map])

            print('About to start server.')
            server_process = multiprocessing.Process(
                name='server', target=run_simg_server, args=(self.simg_loc, self.osrm_map))

            print('Starting server....')
            server_process.start()
            self.process = server_process

            time.sleep(2)

            if server_process.is_alive() and requests.get("http://%s:%d" % (self.ghost, self.gport)).status_code == 400:
                print( "The routing server \"http://%s:%d\" starts running" % (self.ghost, self.gport) )
            else:
                raise Exception("Map could not be loaded")

        else: # If we are running locally and do not need to use singularity to access osrm-backend
            # check file
            try:
                p = Popen([self.exe_loc, '-v'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                output = p.communicate()[0].decode("utf-8")
            except FileNotFoundError:
                output = ""
            if osrm_version not in str(output):
                raise Exception("osrm does not have the right version")
            # check no running server
            if self.check_server():
                raise Exception("osrm-routed already running")
            # start server
            p = Popen([self.exe_loc, '-p', str(self.gport), self.map_loc], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            self.pid = p.pid
            time.sleep(2)
            if requests.get("http://%s:%d" % (self.ghost, self.gport)).status_code == 400:
                print( "The routing server \"http://%s:%d\" starts running" % (self.ghost, self.gport) )
            else:
                raise Exception("Map could not be loaded")
    
    # restart the routing server        
    def restart_server(self):
        self.kill_server()
        self.start_server()
    
    # generate the request in url format        
    def create_url(self, olng, olat, dlng, dlat, steps="false", annotations="false"):
        return "http://{0}:{1}/route/v1/driving/{2},{3};{4},{5}?alternatives=false&steps={6}&annotations={7}&geometries=geojson".format(
            self.ghost, self.gport, olng, olat, dlng, dlat, steps, annotations)

    # send the request and get the response in Json format
    def call_url(self, url):
        count = 0
        # while count < 10:
        try:
            response = requests.get(url, timeout=100)
            json_response = response.json()
            code = json_response['code']
            if code == 'Ok':
                return (json_response, True)
            else:
                print("Error: %s" % (json_response['message']))
                return (json_response, False)
        except requests.exceptions.Timeout:
            print(url)
            self.restart_server()
            count += 1
        except Exception as err:
            print("Failed: %s" % (url))
            return (None, False)
        print("The routing server \"http://%s:%d\" failed and has been restarted... :(" % (self.ghost, self.gport) )
        return self.call_url(url)

    # get the best route from origin to destination 
    def get_routing(self, olng, olat, dlng, dlat):
        global ROUTING_COULD_LOOKUP, ROUTING_USES_ENGINE, FOUND_KEYS_DICT, UNFOUND_KEYS_DICT

        origin = (float(olng), float(olat))
        destination = (float(dlng), float(dlat))

        if origin in OD_DIST_DICT and destination in OD_DIST_DICT[origin]:
            ROUTING_COULD_LOOKUP += 1
        else:
            ROUTING_USES_ENGINE += 1

        url = self.create_url(olng, olat, dlng, dlat, steps="true", annotations="false")
        (response, code) = self.call_url(url)
        if code:
            route = response['routes'][0]['legs'][0]

            # For testing
            total_congested_tt = 0
            total_uncongested_tt = route['duration'] # equal to the sum of the step durations

            # Replace the durations from OSRM freeflow travel with Google Maps based congested travel from dictionary
            for step in route['steps']:
                start_loc = step['intersections'][0]['location']
                slng = round(start_loc[0], LATLNG_PRECISION)
                slat = round(start_loc[1], LATLNG_PRECISION)
                end_loc = step['intersections'][-1]['location']
                elng = round(end_loc[0], LATLNG_PRECISION)
                elat = round(end_loc[1], LATLNG_PRECISION)
                link_key = (slng, slat, elng, elat)

                uncongested_tt = step['duration']

                try:
                    congested_tt = LINK_TRAFFIC_DICT[link_key]
                    if link_key not in FOUND_KEYS_DICT.keys():
                        FOUND_KEYS_DICT[link_key] = [step['distance'], 0]
                    FOUND_KEYS_DICT[link_key][1] += 1

                    # print('Link {} has congested TT: {} but OSRM duration: {}'.format(link_key, congested_tt, step['duration']))

                    step['duration'] = congested_tt

                    # For testing
                    total_congested_tt += congested_tt
                except KeyError:
                    congested_tt = uncongested_tt
                    total_congested_tt += congested_tt
                    if (slng, slat) != (elng, elat):    
                        if link_key not in UNFOUND_KEYS_DICT.keys():
                            UNFOUND_KEYS_DICT[link_key] = [step['distance'], 0]
                        UNFOUND_KEYS_DICT[link_key][1] += 1

                # assert congested_tt >= uncongested_tt

            # assert total_congested_tt >= total_uncongested_tt

            # Change route duration to sum of steps' durations after Google Maps adjustment
            route['duration'] = sum([step['duration'] for step in route['steps']])

            # Test to make sure this worked correctly
            assert route['duration'] == total_congested_tt

            # Record influence of congestion on route travel times
            with open('output/congested-vs-normal-durations.csv', 'a+', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([olat, olng, dlat, dlng, uncongested_tt, total_congested_tt])

            return route
        else:
            return None
    
    # get the distance of the best route from origin to destination
    # if road network is not enabled, return Euclidean distance
    def get_distance(self, olng, olat, dlng, dlat, use_engine=True):
        global DISTANCE_USES_LOOKUP, DISTANCE_USES_ENGINE

        origin = (float(olng), float(olat))
        destination = (float(dlng), float(dlat))
        if origin in OD_DIST_DICT and destination in OD_DIST_DICT[origin]:
            DISTANCE_USES_LOOKUP += 1
            return OD_DIST_DICT[origin][destination]
        else:
            DISTANCE_USES_ENGINE += 1

        if IS_ROAD_ENABLED and use_engine:
            url = self.create_url(olng, olat, dlng, dlat, steps="false", annotations="false")
            (response, code) = self.call_url(url)
            if code:
                return response['routes'][0]['distance']
            else:
                return None
        else:
            return (6371000*2*math.pi/360 * np.sqrt( (math.cos((olat+dlat)*math.pi/360)*(olng-dlng))**2 + (olat-dlat)**2))
    
    # get the duration of the best route from origin to destination
    # if road network is not enabled, return the duration based on Euclidean distance and constant speed   
    def get_duration(self, olng, olat, dlng, dlat, use_engine=True):
        global DURATION_USES_LOOKUP, DURATION_USES_ENGINE

        origin = (float(olng), float(olat))
        destination = (float(dlng), float(dlat))
        if origin in OD_DRTN_DICT and destination in OD_DRTN_DICT[origin]:
            DURATION_USES_LOOKUP += 1
            return OD_DRTN_DICT[origin][destination]
        else:
            DURATION_USES_ENGINE += 1

        if IS_ROAD_ENABLED and use_engine:
            url = self.create_url(olng, olat, dlng, dlat, steps="false", annotations="false")
            (response, code) = self.call_url(url)
            if code:
                return response['routes'][0]['duration']
            else:
                return None
        else:
            return self.get_distance(olng, olat, dlng, dlat, use_engine=use_engine) / self.cst_speed
    
    # get both distance and duration
    def get_distance_duration(self, olng, olat, dlng, dlat, use_engine=True):
        global DISTDRTN_USES_LOOKUP, DISTDRTN_USES_ENGINE

        origin = (float(olng), float(olat))
        destination = (float(dlng), float(dlat))
        if origin in OD_DRTN_DICT and destination in OD_DRTN_DICT[origin] and origin in OD_DIST_DICT and destination in OD_DIST_DICT[origin]:
            DISTDRTN_USES_LOOKUP += 1
            # distance = OD_DIST_DICT[origin][destination]
            # duration = OD_DRTN_DICT[origin][destination]
            # with open('output/distance-duration.csv', 'a+', newline='') as csvfile:
            #     writer = csv.writer(csvfile)
            #     writer.writerow([float(distance)/float(duration)])
            # return (distance, duration)
            return (OD_DIST_DICT[origin][destination], OD_DRTN_DICT[origin][destination])
        else:
            DISTDRTN_USES_ENGINE += 1

        print('get_distance_duration call not using engine')
        if IS_ROAD_ENABLED and use_engine:
            url = self.create_url(olng, olat, dlng, dlat, steps="false", annotations="false")
            (response, code) = self.call_url(url)
            if code:
                # distance = response['routes'][0]['distance']
                # duration = response['routes'][0]['duration']

                # with open('output/distance-duration.csv', 'a+', newline='') as csvfile:
                #     writer = csv.writer(csvfile)
                #     writer.writerow([float(distance)/float(duration)])

                # return (distance, duration)
                return (response['routes'][0]['distance'], response['routes'][0]['duration'])
            else:
                return None
        else:
            return self.get_distance(olng, olat, dlng, dlat), self.get_duration(olng, olat, dlng, dlat) 

    def print_lookup_stats(self, lookup_stats_file):
        print('get_distance using lookup table: {}'.format(DISTANCE_USES_LOOKUP), file=open(lookup_stats_file, 'w+'))
        print('get_duration using lookup table: {}'.format(DURATION_USES_LOOKUP), file=open(lookup_stats_file, 'a+'))
        print('get_distance_duration using lookup table: {}'.format(DISTDRTN_USES_LOOKUP), file=open(lookup_stats_file, 'a+'))
        print('get_distance using routing engine: {}'.format(DISTANCE_USES_ENGINE), file=open(lookup_stats_file, 'a+'))
        print('get_duration using routing engine: {}'.format(DURATION_USES_ENGINE), file=open(lookup_stats_file, 'a+'))
        print('get_distance_duration using routing engine: {}'.format(DISTDRTN_USES_ENGINE), file=open(lookup_stats_file, 'a+'))
        print('get_routing that could use lookup table: {}'.format(ROUTING_COULD_LOOKUP), file=open(lookup_stats_file, 'a+'))
        print('get_routing that can\'t use lookup table: {}'.format(ROUTING_USES_ENGINE), file=open(lookup_stats_file, 'a+'))

    def print_key_stats(self, key_stats_file, found_keys_file=None, unfound_keys_file=None):
        global FOUND_KEYS_DICT, UNFOUND_KEYS_DICT

        total_found_key_calls = 0
        if found_keys_file:
            with open(found_keys_file, 'a+', newline='') as f:
                writer = csv.writer(f)
                for key in FOUND_KEYS_DICT.keys():
                    key_row = list(key)
                    key_row.append(FOUND_KEYS_DICT[key][0])
                    key_row.append(FOUND_KEYS_DICT[key][1])
                    writer.writerow(key_row)

                    total_found_key_calls += FOUND_KEYS_DICT[key][1]

        total_unfound_key_calls = 0
        if unfound_keys_file:
            with open(unfound_keys_file, 'a+', newline='') as f:
                writer = csv.writer(f)
                for key in UNFOUND_KEYS_DICT.keys():
                    key_row = list(key)
                    key_row.append(UNFOUND_KEYS_DICT[key][0])
                    key_row.append(UNFOUND_KEYS_DICT[key][1])
                    writer.writerow(key_row)

                    total_unfound_key_calls += UNFOUND_KEYS_DICT[key][1]

        print('unique links with traffic data used: {}'.format(len(FOUND_KEYS_DICT)), file=open(key_stats_file, 'w+'))
        print('number of observations on links with traffic data: {}'.format(total_found_key_calls), file=open(key_stats_file, 'a+'))
        print('unique links without traffic data used: {}'.format(len(UNFOUND_KEYS_DICT)), file=open(key_stats_file, 'a+'))
        print('number of observations on links without traffic data: {}'.format(total_unfound_key_calls), file=open(key_stats_file, 'a+'))

        FOUND_KEYS_DICT = dict()
        UNFOUND_KEYS_DICT = dict()