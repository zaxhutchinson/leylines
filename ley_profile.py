################################################################
# ley_profile.py
#
# The user's profile class and other profile specific classes.
#
# When new GPS locations come into the server for a specific client
# they are added first to the unexamined path. The analyzer on its
# next run, calculates a new deviation and adds them to the current_path.
# This is done to keep the quad tree clean, i.e. only containing
# locations that have been determined to be "ok".
#
#
################################################################
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

# A contact for defcon alerts.
class Contact:
	def __init__(self, typ = "email", addr="", defcon=10):
		# Email or phone number?
		self.typ = typ

		# Address (email or phone)
		self.addr = addr

		# Defcon level at which the contact should be alerted.
		self.defcon = defcon

		# If the user was alerted, when? So we don't
		# keep sending alerts too often.
		self.last_alert_time_stamp = 0

# The user's preferences:
# Stores all the preferences created by the user.
class Preferences:
	def __init__(self):
		# The average threshold of all contacts
		self.average_defcon_threshold = 5.0

		# Lack of movement threshold and importance
		self.max_time_unmoved = 0.0
		self.weight_max_time_unmoved = 0

		# Friend list, of userids
		self.friend_list = []

		# Contact list
		self.defcon_contact_list = []
		
		# How often is the client logging and sending GPS data
		# How often should we send an alert when a threshold is reached.
		self.pref_key_alert_frequency=10800
		self.pref_key_gps_collect_frequency=300
		self.pref_key_gps_send_frequency=3600

		# Enables/disables all tracker settings
		# How long until this sets off an alert
		self.pref_key_tracker_settings=False
		self.pref_key_tracker_disabled_duration_setting=3600

		# Enables/disables inactivity tracking
		# Inactivity alert theshold
		self.pref_key_tracker_inactive_setting=False
		self.pref_key_tracker_inactive_duration_setting=604800

		# Multiplier for how long to go without messages
		# from the client without sending alert
		self.pref_key_tracker_response_setting=False
		self.pref_key_tracker_response_misses_setting=3
		self.pref_key_tracker_settings_alert=""

		self.pref_key_lifestyle_setting=0
		self.pref_key_sensitivity_setting=0

		# Low battery alert
		self.pref_key_battery_settings=False
		self.pref_key_battery_level_settin=20
		self.pref_key_battery_level_alert=""
		self.pref_key_battery_importance=0.5

		# MAX DISTANCE TO KNOWN QUAD
		self.pref_key_distance_settings=False
		self.pref_key_distance_importance=10
		self.pref_key_distance_deviation_setting=1000
		self.pref_key_distance_deviation_alert=""

		# MAX TOTAL DISTANCE OF UNKNOWN PATH
		self.pref_key_distance_total_settings=False
		self.pref_key_distance_total_importance=10
		self.pref_key_distance_deviation_total_setting=1000
		self.pref_key_distance_deviation_total_alert=""
		
		# Location specific alert settings
		self.pref_key_location_settings=False
		self.pref_key_location_importance=10
		self.pref_key_location_distance_setting=1000
		self.pref_key_location_time_setting=3600
		self.pref_key_location_settings_alert=""

		# Time alert settings.
		self.pref_key_time_settings=False
		self.pref_key_time_importance=10
		self.pref_key_time_deviation_setting=10800
		self.pref_key_time_deviation_alert=""
		
		self.pref_key_tracker_disabled_setting=False

		#############################################
		# PHONE SETTINGS THAT ARE STORED DIFFERENTLY
		# SERVER SIDE. HERE FOR REFERENCE ONLY
		#pref_key_contact3_alert_setting=3
		#pref_key_contact2_alert_setting=3
		#pref_key_contact1_alert_setting=3
		#pref_key_contact1_type_setting=email
		#pref_key_contact3_info_setting=
		#pref_key_contact1_info_setting=
		#pref_key_contact2_info_setting=
		#pref_key_contact3_type_setting=email
		#pref_key_contact_self_setting=false
		#pref_key_contact2_type_setting=email
		#pref_key_advanced_settings=false
		############################################

# The status of the user
class Status:
	def __init__(self):
		# Current Defcon level
		self.current_defcon = 0

		# Any time defcon changes, we store it and the time.
		self.defcon_history = deque(( self.current_defcon,int(time.time()) ))
		
		# Total distance of current unknown path
		self.unknown_path_total_distance = 0.0

		# When were we in a last known location?
		self.time_stamp_last_known_location = 0.0
		
		# Current danger level
		self.danger_level = 0.0

		#True if the user is being tracked. False otherwise.
		self.isTracking = True 
		
		#Saves the time that the tracker was disabled.
		#Used to determine how long the tracker was disabled.
		self.time_Disabled = 0.0

		# When did we receive the last message from the client
		self.timestamp_last_message = time.time()

		# Have we sent an alert?
		self.alert_has_been_sent = False

	# Updates the Defcon level
	# TODO: Change name of function, is a helper to the
	# function updateDefcon below
	def getDefconForDangerLevel(self):
		
		defcon = 0

		if( self.danger_level >= config.DEFCON_1 ):
			defcon = 1
		elif( self.danger_level >= config.DEFCON_2 ):
			defcon = 2
		elif( self.danger_level >= config.DEFCON_3 ):
			defcon = 3
		elif( self.danger_level >= config.DEFCON_4 ):
			defcon = 4
		elif( self.danger_level >= config.DEFCON_5 ):
			defcon = 5
		elif( self.danger_level >= config.DEFCON_6 ):
			defcon = 6
		elif( self.danger_level >= config.DEFCON_7 ):
			defcon = 7
		elif( self.danger_level >= config.DEFCON_8 ):
			defcon = 8
		elif( self.danger_level >= config.DEFCON_9 ):
			defcon = 9
		elif( self.danger_level >= config.DEFCON_10 ):
			defcon = 10

		return defcon

	# Call to update the defcon level based on the current
	# danger_level.
	def updateDefcon(self):
		tmp_defcon = self.current_defcon

		self.current_defcon = self.getDefconForDangerLevel()

		# if we have a new defcon, record it and the time stamp in our history
		if( tmp_defcon != self.current_defcon ):
			self.current_defcon = tmp_defcon
			self.defcon_history.append( (self.current_defcon, int(time.time()) ) )

# The user profile class
class Profile:
	def __init__(self, uid, coord, data, first_name="Edmund", last_name="Blackadder"):
		
		# User ID, name
		self.uid = uid
		self.first_name = first_name
		self.last_name = last_name

		# Hackery, but set to 1. The 0th dataID will be taken by the first
		# data entry done on profile creation
		self.dataID = 1

		# The quadtree and the flattened tree. NOTE: rename tree_as_list
		self.tree_as_list = {}
		self.tree = quadtree.QuadTree(coord, data)

		# Preferences object
		self.preferences = Preferences()

		# The current path and unexamined path.
		self.current_path = deque()
		self.unexamined_path = deque()

		# Status object
		self.status = Status()
		
		# Has the profile been updated, i.e. should it be
		# examined by the analyzer?
		self.updated = True

		# When updating the dataID, we need to lock the profile.
		self.locked = False

	# ===============================================================
	# PREFERENCES GET/SET
	def getMaxDistanceToKnownQuad(self):
		return self.preferences.pref_key_distance_deviation_setting
	def setMaxDistanceToKnownQuad(self, dist):
		self.preferences.pref_key_distance_deviation_setting = dist
	def getWeightDistanceToKnownQuad(self):
		return self.preferences.pref_key_distance_importance
	def setWeightDistanceToKnownQuad(self, weight):
		self.preferences.pref_key_distance_importance = weight

	def getMaxTimeOnUnknownPath(self):
		return self.preferences.pref_key_time_deviation_setting
	def setMaxTimeOnUnknownPath(self, time):
		self.preferences.pref_key_time_deviation_setting = time
	def getWeightTimeOnUnknownPath(self):
		return self.preferences.pref_key_time_importance
	def setWeightTimeOnUnknownPath(self, weight):
		self.preferences.pref_key_time_importance = weight

	def getMaxDistanceOfUnknownPath(self):
		return self.preferences.pref_key_distance_deviation_total_setting
	def setMaxDistanceOfUnknownPath(self, dist):
		self.preferences.pref_key_distance_deviation_total_setting = dist
	def getWeightDistanceOfUnknownPath(self):
		return self.preferences.pref_key_distance_total_importance
	def setWeightDistanceOfUnknownPath(self, weight):
		self.preferences.pref_key_distance_total_importance = weight

	def getAverageDefconThreshold(self):
		return self.preferences.average_defcon_threshold
	def setAverageDefconThreshold(self, avg_defcon):
		total_defcon = 0
		num_contacts = len(self.preferences.defcon_contact_list)
		for contact in self.preferences.defcon_contact_list:
			total_defcon += contact.defcon
		if(num_contacts > 0):
			self.preferences.average_defcon_threshold = int(total_defcon / num_contacts)

	def getAlertFrequency(self):
		return self.preferences.pref_key_alert_frequency
	def setAlertFrequency(self, time):
		self.preferences.pref_key_alert_frequency = time
	def getGPSCollectionFrequency(self):
		return self.preferences.pref_key_gps_collect_frequency
	def setGPSCollectionFrequency(self, time):
		self.preferences.pref_key_gps_collect_frequency = time
	def getGPSSendFrequency(self):
		return self.preferences.pref_key_gps_send_frequency
	def setGPSSendFrequency(self, time):
		self.preferences.pref_key_gps_send_frequency = time

	def getFriendList(self):
		return self.preferences.friend_list
	def getFriendRange(self):
		return self.preferences.friend_range
	def setFriendRange(self, new_range):
		self.preferences.friend_range = new_range
	
	def getDefconContactList(self):
		return self.preferences.defcon_contact_list
	def addContactToDefconContactList(self, contact):
		self.preferences.defcon_contact_list.append( contact )

	def getMaxDisconnectTime(self):
		return self.preferences.pref_key_tracker_response_misses_setting * self.preferences.pref_key_gps_send_frequency

	def getIsTrackingDisconnect(self):
		return self.preferences.pref_key_tracker_response_setting
	def setIsTrackingDisconnect(self, setting):
		self.preferences.pref_key_tracker_response_setting = setting

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
		self.status.danger_level = danger_level

	def updateDefconLevel(self):
		self.status.updateDefcon()
	def getCurrentDefconLevel(self):
		return self.status.current_defcon
	def setCurrentDefconLevel(self, new_defcon):
		self.status.current_defcon = new_defcon
	def isDefconThresholdReached(self):
		if( self.getCurrentDefconLevel() >= self.getDefconThreshold() ):
			return True
		else:
			return False

	def getIsTracking(self):
		return self.status.isTracking
	def setIsTracking(self, T):
		self.status.isTracking = T
	def flipIsTracking(self):
		self.status.isTracking = not self.status.isTracking
		return self.status.isTracking
		
	def getTimeDisabled(self):
		return self.status.time_Disabled
	def setTimeDisabled(self, Td):
		self.status.time_Disabled = Td

	def getTimeStampOfLastMessage(self):
		return self.status.timestamp_last_message
	def setTimeStampOfLastMessage(self):
		self.status.timestamp_last_message = time.time()

	#############################################################
	# Profile specific functions

	# Get the profiles user id
	def getUID(self):
		return self.uid

	# Atomic function to get and update dataID
	def getNextDataID(self):
		while(self.isLocked()):
			None
		self.lock()
		next_data_id = self.dataID
		self.dataID += 1
		self.unlock()
		return next_data_id

	# We don't want to save the quadtree to disk
	def __getstate__(self):
		state = self.__dict__.copy()
		del state['tree']
		return state
	def __setstate__(self, d):
		self.__dict__.update(d)

	# Save/Load functions
	@classmethod
	def load(cls, filename):
		input_file = open(filename, 'rb')
		return pickle.load(input_file)

	# Kicks off the process of rebuilding the tree when loaded.
	def rebuildTree(self, tree_as_dict):
		self.tree.rebuildQuadTree(tree_as_dict)
		self.dataID = len(tree_as_dict)

	# Save the profile, but don't keep the flattened
	# tree in memory. It's written and then disposed of.
	def save(self):
		output_file = open(self.uid, 'wb')
		self.tree_as_list = self.tree.flattenTree()
		pickle.dump(self, output_file)
		output_file.close()
		self.tree_as_list.clear()
		return

	# Locks, etc.
	def isLocked(self):
		return self.locked
	def unlock(self):
		self.locked = False
	def lock(self):
		self.locked = True

	# Adds new Coord and Data to the unexamined path queue
	# NOTE: This should be the only function called by the Leylines
	#	routine that adds new data from the app. After it's in the
	#	unexamined path, the analyzer takes over, moving the data
	#	toward the tree.
	def addNewUnexaminedLocation( self, coord, data ):
		self.unexamined_path.append( (coord,data) )
		self.updated = True
		return

	# Takes elements of a new contact, makes a new contact
	# and adds it to the defcon contact list.
	def addNewContact( self, typ, addr, defcon ):
		contact = Contact(typ, addr, defcon )
		self.addContactToDefconContactList( contact )

	# Pops and returns the newest location on the current path.
	def getCurrentPathNewestLocation(self):
		if(len(self.current_path) > 0):
			return self.current_path.pop()
		else:
			return None
	# Pops and returns the oldest location on the current path.
	def getCurrentPathOldestLocation(self):
		if(len(self.current_path) > 0):
			return self.current_path.popleft()
		else:
			return None

	# Adds old location back to path
	def returnOldLocationToPath(self, loc):
		self.current_path.appendleft(loc)
		return
	# Adds a new location to path
	def appendToCurrentPathFromWhole(self, loc):
		self.current_path.append(loc)
		return
	def appendToCurrentPathFromParts(self, coord, data):
		self.current_path.append( (coord, data) )
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

	# Interface function between profile and tree.
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


	
