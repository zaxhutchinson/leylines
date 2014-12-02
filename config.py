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
MSG_AWK = 0
MSG_INIT= 1
MSG_PREF = 2
MSG_GPS = 3

DEFCON_1 = 0.80
DEFCON_2 = 0.60
DEFCON_3 = 0.40
DEFCON_4 = 0.20
DEFCON_5 = 0.00
########################################
