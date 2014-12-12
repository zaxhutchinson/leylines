import math
import pickle
import sys
import time
import Queue
from collections import deque
import quadtree
import misc
import alignment
import config


class Contact:
	def __init__(self, email="", defcon=10, msg=""):
		self.email = email
		self.defcon = defcon
		self.msg = msg
		self.last_alert_time_stamp = 0

# The user's preferences
# NOTE:
#	-AND/OR relationships?
class Preferences:
	def __init__(self):
		self.defcon_threshold = 1.0
		self.max_unknown_distance = 0.0
		self.max_distance_to_known_quad = 0.0
		self.max_time_on_unknown_path = 0.0
		self.max_time_unmoved = 0.0
		self.weight_max_unknown_distance = 0
		self.weight_max_distance_to_known_quad = 0
		self.weight_max_unknown_time_elapsed = 0
		self.weight_max_time_unmoved = 0

		self.alert_freq = 0.0
		self.gps_collection_freq = 0.0
		self.gps_send_freq = 0.0

		self.friend_list = []

		self.defcon_contact_list = []
		self.defcon_alert_freq = 3600 # In secs
		
		self.password = 'plan9sucks'

# The status of the user
class Status:
	def __init__(self):
		self.current_defcon = 5
		self.defcon_history = deque(( self.current_defcon,int(time.time()) ))
		self.unknown_path_total_distance = 0.0
		self.time_stamp_last_known_location = 0.0
		self.danger_level = 0.0

		self.alert_has_been_sent = False

	def getDefconForDangerLevel(self, danger_level):
		
		defcon = 0

		if( danger_value >= config.DEFCON_1 ):
			defcon = 1
		elif( danger_value >= config.DEFCON_2 ):
			defcon = 2
		elif( danger_value >= config.DEFCON_3 ):
			defcon = 3
		elif( danger_value >= config.DEFCON_4 ):
			defcon = 4
		elif( danger_value >= config.DEFCON_5 ):
			defcon = 5
		elif( danger_value >= config.DEFCON_6 ):
			defcon = 6
		elif( danger_value >= config.DEFCON_7 ):
			defcon = 7
		elif( danger_value >= config.DEFCON_8 ):
			defcon = 8
		elif( danger_value >= config.DEFCON_9 ):
			defcon = 9
		elif( danger_value >= config.DEFCON_10 ):
			defcon = 10

		return defcon

	def updateDefcon(self, danger_value):
		tmp_defcon = self.current_defcon

		self.current_defcon = self.getDefconForDangerLevel(danger_level)

		# if we have a new defcon, record it and the time stamp in our history
		if( tmp_defcon != self.current_defcon ):
			self.current_defcon = tmp_defcon
			self.defcon_history.append( (self.current_defcon, int(time.time()) ) )


class Profile:
	def __init__(self, uid, first_name, last_name, coord, data):
		self.uid = uid
		self.first_name = first_name
		self.last_name = last_name
		self.tree = QuadTree(coord, data)

		self.preferences = Preferences()

		self.current_path = deque()
		self.unexamined_path = Queue.Queue()

		self.status = Status()
		self.updated = True

	# ===============================================================
	# PREFERENCES GET/SET
	def getMaxDistanceToKnownQuad(self):
		return self.preferences.max_distance_to_known_quad
	def setMaxDistanceToKnownQuad(self, dist):
		self.preferences.max_distance_to_known_quad = dist
	def getMaxTimeOnUnknownPath(self):
		return self.preferences.max_time_on_unknown_path
	def setMaxTimeOnUnknownPath(self, time):
		sellf.preferences.max_time_on_unknown_path = time
	def getMaxDistanceOfUnknownPath(self):
		return self.preferences.max_unknown_distance
	def setMaxDistanceOfUnknownPath(self, dist):
		self.preferences.max_unknown_distance = dist
	def getDefconThreshold(self):
		return self.preferences.defcon_threshold
	def setDefconThreshold(self, defcon):
		self.preferences.defcon_threshold = defcon
	def getAlertFrequency(self):
		return self.preferences.alert_freq
	def setAlertFrequency(self, time):
		self.preferences.alert_freq = time
	def getGPSCollectionFrequency(self):
		return self.preferences.gps_collection_freq
	def setGPSCollectionFrequency(self, time):
		self.preferences.gps_collection_freq = time
	def getGPSSendFrequency(self):
		return self.preferences.gps_send_freq
	def setGPSSendFrequency(self, time):
		self.preferences.gps_send_freq = time
	def getWeightDistanceOfUnknownPath(self):
		return self.preferences.weight_max_unknown_distance
	def setWeightDistanceOfUnknownPath(self, weight):
		self.preferences.weight_max_unknown_distance = weight
	def getWeightDistanceToKnownQuad(self):
		return self.preferences.weight_max_distance_to_known_quad
	def setWeightDistanceToKnownQuad(self, weight):
		self.preferences.weight_max_distance_to_known_quad = weight
	def getWeightTimeOnUnknownPath(self):
		return self.preferences.weight_max_time_unmoved
	def setWeightTimeOnUnknownPath(self, weight):
		self.preferences.weight_max_time_unmoved = weight
	def getFriendRange(self):
		return self.preferences.friend_range
	def setFriendRange(self, new_range):
		self.preferences.friend_range = new_range
	def getDefconContactList(self):
		return self.preferences.defcon_contact_list
	def addContactToDefconContactList(self, contact):
		self.preferences.defcon_contact_list.append( contact )
	def getPassword(self):
		return self.preferences.password
	def setPassword(self, new_password)
		self.preferences.password = password
	# ===============================================================
	# STATUS GET/SET
	def getCurrentUnknownDistance(self):
		return self.status.unknown_path_total_distance
	def getCurrentUnknownPathTimeStamp(self):
		return self.status.time_stamp_last_known_location

	def setUnknownDistance(self, dist):
		self.status.unknown_path_total_distance = dist
		return
	def setUnknownPathTime(self, time):
		self.status.time_stamp_last_known_location = time

	def getCurrentDangerLevel(self):
		return self.status.danger_level
	def setCurrentDangerLevel(self, danger_level):
		self.danger_level = danger_level

	def getCurrentDefconLevel(self):
		return self.status.current_defcon
	def setCurrentDefconLevel(self, new_defcon):
		self.status.current_defcon = new_defcon
	def isDefconThresholdReached(self):
		if( self.getCurrentDefconLevel() >= self.getDefconThreshold() ):
			return True
		else
			return False

	@classmethod
	def load(cls, filename):
		input_file = open(filename, 'rb')
		return pickle.load(input_file)

	def save(self):
		output_file = open(self.uid, 'wb')
		pickle.dump(self, output_file)
		output_file.close()
		return

	# Adds new Coord and Data to the unexamined path queue
	# NOTE: This should be the only function called by the Leylines
	#	routine that adds new data from the app. After it's in the
	#	unexamined path, the analyzer takes over, moving the data
	#	toward the tree.
	def addNewUnexaminedLocation( self, coord, data ):
		self.unexamined_path.put( (coord,data) )
		self.updated = True
		return

	# Takes elements of a new contact, makes a new contact
	# and adds it to the defcon contact list.
	def addNewContact( self, email, defcon_level, msg ):
		contact = Contact(email, defcon_level, msg )
		self.addContactToDefconContactList( contact )

	# Adds the oldest unexamined loc to the current path,
	# enlarging the tuple to include the state: 0 if not in tree, 1 if it is.
	#def popUnexaminedToCurrentPath(self, state_of_path):
	#	loc = self.unexamined_path.popleft()
	#	self.current_path.append( (loc[0], loc[1], state_of_path) )
	#	return
	def getCurrentPathNewestLocation(self):
		return self.current_path.pop()
	def getCurrentPathOldestLocation(self):
		return self.current_path.popleft()
	def returnOldLocationToPath(self, loc):
		self.current_path.appendleft(loc)
		return
	def appendToCurrentPathFromWhole(self, loc):
		self.current_path.append(loc)
		return
	def appendToCurrentPathFromParts(self, coord, data, deviation):
		self.current_path.append( (coord, data, deviation) )
		return

	# Add all current path to the tree, leaving out the state info
	# stored by the current path deque
	def dumpCurrentPath(self):
		while(len(self.current_path) > 0):
			loc = self.current_path.popleft()
			self.addNewData(loc[0],loc[1])
	# Add a single location stripping out the deviation info
	def dumpLocation(self, loc):
		self.addNewData(loc[0], loc[1])


	def addNewData( self, coord, data ):
		return self.tree.addNewData( coord, data )

	# ====================================================================== #
	# Interface functions for access to the tree. Most of these just
	# call identical tree functions.
	def isKnownCoord(self, coord):
		if(self.tree.isKnownCoord(coord)):
			return 0
		else:
			return 1

	# How close is the nearest quad in the tree in meters
	def getDistanceToKnownLocation(self, coord):
		return self.tree.getDistanceToGoodQuad(coord)

	# Has the user changed position from the last logged location
	def hasLocationChanged(self, coord):
		return self.tree.isCoordInLastAddedQuad(coord)

	# Get the last entry into the quadtree
	def getLastCoordInQuadTree(self):
		return self.tree.getPrevEntryLocationMidPoint()


	
