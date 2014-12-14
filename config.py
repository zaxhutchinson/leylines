MINUTES_TO_METERS = 1852.0
DEGREES_TO_MINUTES = 60.0
EARTH_RADIUS = 6371000
DIAMETER_EXP = 16
QUAD_DIAMETER = 2**DIAMETER_EXP
RADIUS_EXP = 15
QUAD_RADIUS = 2**RADIUS_EXP
MIN_EXP = 5
QUAD_MIN = 2**MIN_EXP
PI = 3.14159265358979323846264338327

DAY_IN_SECS = 86400

MIN_VISITS_TO_CREATE_MEGALITH = 2

TIME_BLOCK = 15

# This is multiplied by the GPS send frequency in order
# to determine the time span in which to consider
# recent GPS entries for a new danger level computation. 
DANGER_LEVEL_TIME_BLOCK = 2.0

########################################
### DO NOT CHANGE VALUES ONCE IN USE ###
HOST = ''
PORT = 65006
# MSG_AWK = 
MSG_TRACK = 'T'
MSG_REFRESH = 'R'
MSG_LOC = 'L'
MSG_PREF = 'S'
MSG_POS = 'G'
MSG_INIT = 'I'

DEFCON_1 = 0.1
DEFCON_2 = 0.2
DEFCON_3 = 0.3
DEFCON_4 = 0.4
DEFCON_5 = 0.5
DEFCON_6 = 0.6
DEFCON_7 = 0.7
DEFCON_8 = 0.8
DEFCON_9 = 0.9
DEFCON_10 = 1.0
########################################
