"""
constants are found here
"""

from lib.Demand import *
from lib.ODDistances import od_distances as OD_DIST_DICT
from lib.ODDurations import od_durations as OD_DRTN_DICT

# List of tuples of two random seeds for use in the Model
SEEDS = [(750647, 605886),
		 (989792, 939889),
		 (97990, 451740),
		 (174830, 844466),
		 (889073, 609353),
		 (393230, 61254),
		 (507793, 791264),
		 (995524, 156179),
		 (503345, 989240),
		 (82059, 600134),
		 (628566, 635310),
		 (550825, 342710),
		 (478102, 718818),
		 (737520, 954525),
		 (197916, 748653),
		 (426615, 270593),
		 (31274, 936874),
		 (4077, 648826),
		 (426811, 717490),
		 (603262, 536182),
		 (266333, 859300),
		 (17388, 605667),
		 (413539, 779558),
		 (408962, 94663),
		 (229152, 396390),
		 (588632, 193445),
		 (246887, 574366),]

# Use the above list or generate and record random seeds
USE_SEEDS = False

#Fare
price_base = 0.831 # dollars/ per trip 
price_unit_time = 0.111 # dollars/min
price_unit_distance = 0.547 # dollars/km 
sharing_discount = 0.75 # 25% discount 
transit_connect_discount = 1.33 # dollars
min_cost_avpt = 1.73 # dollars 
FARE = [price_base, price_unit_time, price_unit_distance, sharing_discount, transit_connect_discount, min_cost_avpt]

# fleet size and vehicle capacity
FLEET_SIZE= [200]
VEH_CAPACITY = 4

# ASC and the nickname of the run
ASC_AVPT = -3.5
ASC_NAME = "AVPT" + str(ASC_AVPT)

# cost-benefit analysis
COST_BASE = 0.0
COST_MIN = 0.061
COST_KM = 0.289
PRICE_BASE = 0.831
PRICE_MIN = 0.111
PRICE_KM = 0.527
PRICE_DISC = 0.75

# initial wait time and detour factor when starting the interaction
INI_WAIT = 400
INI_DETOUR = 1.25

# number of iteration steps
ITER_STEPS = 10

# warm-up time, study time and cool-down time of the simulation (in seconds)
T_WARM_UP = 60*30
T_STUDY = 60*60
T_COOL_DOWN = 60*30
T_TOTAL = (T_WARM_UP + T_STUDY + T_COOL_DOWN)

# methods for vehicle-request assignment and rebalancing
# ins = insertion heuristics
# sar = simple anticipatory rebalancing, orp = optimal rebalancing problem, dqn = deep Q network
MET_ASSIGN = "ins"
MET_REOPT = "no"
MET_REBL = "sar"

# intervals for vehicle-request assignment and rebalancing
INT_ASSIGN = 30
INT_REBL = 150

# if road network is enabled, use the routing server; otherwise use Euclidean distance
IS_ROAD_ENABLED = True
USE_ENGINE_FOR_INSERTION = False
# if true, activate the animation
IS_ANIMATION = False

# Enables diagnostics reporting like the number of links that were found in the lookup table and the number of calls to the routing engine
DIAGNOSTICS_ENABLED = True
# Enables printing of state of simulation every update
PRINT_PROGRESS = False

# Specifies the precision of latitude/longitude for finding a given link in the O/D table
# This is the number of decimal places at which to round
# See https://en.wikipedia.org/wiki/Decimal_degrees#Precision for insight
LATLNG_PRECISION = 4

# maximum detour factor and maximum wait time window
MAX_DETOUR = 1.5
MAX_WAIT = 60*10

# constant vehicle speed when road network is disabled (in meters/second)
CST_SPEED = 9 # Based on empirical results from routing engine
# CST_SPEED = 6

# probability that a request is sent in advance (otherwise, on demand)
PROB_ADV = 0.0
# time before which system gets notified of the in-advance requests
T_ADV_REQ = 60*30

# coefficients for wait time and in-vehicle travel time in the utility function
COEF_WAIT = 1.5
COEF_INVEH = 1.0

# map width and height
MAP_WIDTH = 5.52
MAP_HEIGHT = 6.63

# coordinates
# (Olng, Olat) lower left corner
Olng = -0.02
Olat = 51.29
# (Dlng, Dlat) upper right corner
Dlng = 0.18
Dlat = 51.44
# number of cells in the gridded map
Nlng = 10
Nlat = 10
# number of moving cells centered around the vehicle
Mlng = 5
Mlat = 5
# length of edges of a cell
Elng = 0.02
Elat = 0.015