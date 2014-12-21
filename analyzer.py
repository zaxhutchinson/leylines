######################################################################
# Project Leylines
# Analyzer
# 
# Contributors: 
#	Zachary Hutchinson
#	Tamel Nash
#	Travis Geeting
#	Cameron Rivera
#
# Analyzer consists of a series of independent functions that handle
# the analysis of profile and path states, updating danger levels,
# defcon levels and sending alerts.
#
# See individual functions for further descriptions.
#######################################################################

import time
import math
import config
import alert
from collections import deque

#######################################################################
# Helper functions for GPS and time differences
def toDegrees( radians ):
	return radians * 180.0 / config.PI

def toRadians( degrees ):
	return degrees * config.PI / 180.0

def distanceBetweenTwoPoints( GPSone, GPStwo ):
	lat1 = toRadians(GPSone.latitude)
	lat2 = toRadians(GPStwo.latitude)
	long1 = toRadians(GPSone.longitude)
	long2 = toRadians(GPStwo.longitude)

	delta_lat = (lat2 - lat1)
	delta_long = (long2 - long1)

	alpha = math.pow(math.sin(delta_lat / 2.0), 2.0) + \
				math.cos(lat1) * math.cos(lat2) * \
				math.pow(math.sin(delta_long / 2.0), 2.0)

	beta = 2 * math.atan2( math.sqrt(alpha), math.sqrt(1 - alpha) )

	return config.EARTH_RADIUS * beta

def calculateTimeDeviation( max_time, time ):
	return max_time - time
def calculateRelativeDistanceDeviation( max_dist, dist ):
	return max_dist - dist
def calculateTotalDistanceDeviation( max_dist, dist ):
	return max_dist - dist
########################################################################

# Examines the unexamined_path of the profile and adds it to the
# current_path. It's main job is to calculate the deviation number
# of each individual logged location with respect to distance and time.
def examineNewLocation( profile, log ):

	# Since this is a while something loop, we need to have a max number of
	# iterations or else there is a theoretical risk, it never terminates
	# if someone's app continues to update the queue with GPS coords. 
	count = 0

	# Process a max of ten unexamined locations
	while( ( len(profile.unexamined_path) > 0 ) and count < 100):

		log.write("#######################################\n")

		new_loc = profile.unexamined_path.popleft()
		
		# Get path state (either 0 or 1)
		# If it's 0, then we're in a location we've been before
		# If it's 1, then we're in an unfamiliar location, so
		# we need to find the real deviation based on the max distance
		# from nearest familiar location.
		state_of_path = profile.isKnownCoord(new_loc[0])

		# Add to current path
		# profile.popUnexaminedToCurrent(state_of_path)

		total_deviation = 0.0

		# We have been in this location before
		if(state_of_path == 0):
			profile.setUnknownDistance(0.0)
			profile.setUnknownPathTime(new_loc[1].time)

		else:
			# How far is this coordinate from a known location?
			distance_to_known_location = profile.getDistanceToKnownLocation(new_loc[0])

			log.write("DIST TO KNOWN LOCATION: " + str(distance_to_known_location) + "\n")

			# Calculate the relative distance deviation
			raw_deviation_relative_distance = float(distance_to_known_location) / float(profile.getMaxDistanceToKnownQuad())

			# Get previous location added to current path
			previous_location = profile.getCurrentPathNewestLocation()
			
			prev_coord = None

			if(previous_location != None):
				# Snag the prev_coord
				#log.write("TAKEN FROM CUR PATH\n")
				prev_coord = previous_location[0]

				# Return previous_location to current path
				profile.appendToCurrentPathFromWhole(previous_location)
			else:
				#log.write("TAKEN FROM QT\n")
				# Get the last coord added to the quad tree.
				prev_coord = profile.getLastCoordInQuadTree()

			if(prev_coord == None):
				raise

			# Calculate and update total distance of this unknown path
			present_dist = profile.getCurrentUnknownDistance() + distanceBetweenTwoPoints(new_loc[0], prev_coord)
			log.write("PREV_COORD: " + str(prev_coord.latitude) + " " + str(prev_coord.longitude))
			log.write("NEW_LOC: " + str(new_loc[0].latitude) + " " + str(new_loc[0].longitude))

			log.write("TOTAL DISTANCE ON UNKNOWN PATH ( " + str(profile.getCurrentUnknownDistance()) + " + " + str(distanceBetweenTwoPoints(new_loc[0], prev_coord)) + " = " + str(present_dist) + "\n")

			# Update the new unknown distance
			profile.setUnknownDistance(present_dist)

			# Calculate deviation for total distance
			raw_deviation_total_distance = float(present_dist) / float(profile.getMaxDistanceOfUnknownPath())

			# Get time on unknown path. In seconds...probably.
			time_on_unknown_path = new_loc[1].time - profile.getCurrentUnknownPathTimeStamp()

			log.write("TOTAL TIME ON UNKNOWN PATH: " + str(time_on_unknown_path) + "\n")

			# Calc the time deviation
			raw_deviation_time = float(time_on_unknown_path) / float(profile.getMaxTimeOnUnknownPath())

			# Get each deviation adjusted by user set weight
			deviation_relative_distance = raw_deviation_relative_distance *	profile.getWeightDistanceToKnownQuad()
			deviation_total_distance = raw_deviation_total_distance * profile.getWeightDistanceOfUnknownPath()
			deviation_total_time = raw_deviation_time *	profile.getWeightTimeOnUnknownPath()

			log.write("REL DIST DEV: " + str(deviation_relative_distance) + "\n")
			log.write("TOTAL DIST DEV: " + str(deviation_total_distance) + "\n")
			log.write("TOTAL TIME DEV: " + str(deviation_total_time) + "\n")

			# Total possible weight when raw_deviations total 1.0
			total_weight = profile.getWeightDistanceToKnownQuad() + profile.getWeightDistanceOfUnknownPath() + profile.getWeightTimeOnUnknownPath()
			
			total_deviation = (deviation_relative_distance + deviation_total_distance + deviation_total_time) / total_weight

			log.write("TOTAL DEVIATION: " + str(total_deviation) + "\n")
			log.write("CURRENT DEFCON LEVEL: " + str(profile.getCurrentDefconLevel()) + "\n")

			new_loc[1].deviation = total_deviation

		profile.appendToCurrentPathFromWhole( new_loc )

		# Unlock Queue
		# profile.unexamined_path.task_done()

		# Last thing
		count += 1

	if( len(profile.unexamined_path) == 0 ):
		profile.updated = False

 			
def examineCurrentPath( profile, log ):

	length = len(profile.current_path)
	print("LEN CURRENT PATH: " + str(length))

	if(length > 0):

		# Where we'll store location's when we pull them off the path
		temp_deque = deque()

		count = 0

		# Get the last location we added to the current path
		last_loc = profile.getCurrentPathNewestLocation()
		if(last_loc != None):

			count += 1

			temp_deque.append(last_loc)

			# Get the time in secs of ( last_time - GPS Send Freq )
			max_time = last_loc[1].time - (config.DANGER_LEVEL_TIME_BLOCK * profile.getGPSSendFrequency())

			# Loop while we haven't reached the beginning of the queue
			# and the time of the present element we're inspecting is
			# is not older than max_time
			while( True ):
				#Get next oldest location
				last_loc = profile.getCurrentPathNewestLocation()
				if(last_loc == None):
					break
				# If it falls within the GPS send time...
				if(last_loc[1].time > max_time):
					count += 1

					# Add it to the temp queue
					temp_deque.append(last_loc)
				
				else:
					profile.appendToCurrentPathFromWhole(last_loc)
					break

		print("TEMP_DEQUE = " + str(count))
		
		# Non-local storage for the loop
		number_inspected = 0
		total_deviation = 0.0

		# For everything newer than last time - GPS send freq
		# Accumulate and add back to the current path in order
		while( len(temp_deque) > 0 ):
			loc = temp_deque.popleft()

			number_inspected += 1
			total_deviation += loc[1].deviation

			profile.appendToCurrentPathFromWhole(loc)

		# Use what we found to calculate newest danger level

		print("DEVIATION: " + str(total_deviation) + "|" + str(number_inspected))

		if(number_inspected > 0):
			profile.setCurrentDangerLevel( float(total_deviation) / float(number_inspected) )

			print("DANGER_LEVEL: " + str(profile.getCurrentDangerLevel()))

			profile.updateDefconLevel()

			#log.write("CURRENT DEFCON LEVEL: " + str(profile.getCurrentDefconLevel()))


# Remove older additions from the current path depending on the current defcon level.
def purgeCurrentPathToTree( profile ):

	# If the current defcon level is above the defcon threshold, do not
	# send any data to the quad tree.
	if(profile.getCurrentDefconLevel() >= profile.getAverageDefconThreshold()):
		return	

	# If the defcon level is five, we don't need to worry too much
	# Remove from the current path queue all location entries older
	# than the current GPS send frequency.	
	elif(profile.getCurrentDefconLevel() < 1):
		
		oldest_loc = profile.getCurrentPathOldestLocation()
		if(oldest_loc != None):
			purge_to_date = oldest_loc[1].time + profile.getGPSSendFrequency()

			# The newest date we want to purge is the present time minus
			# the GPS Send Frequency. If purge_to_date is more recent than that
			# just the max.
			max_purge_to_date = (int(time.time()) - profile.getGPSSendFrequency() )
			if(purge_to_date > max_purge_to_date ):
				purge_to_date = max_purge_to_date

			# Purge everything up to the purge date and dump it into the quadtree.
			while( (oldest_loc[1].time < purge_to_date) ):
				profile.dumpLocation(oldest_loc)

				oldest_loc = profile.getCurrentPathOldestLocation()

				if(oldest_loc == None):
					break

	# Above 1 but below threshold:
	# Only purge data more than 24 hours old.
	else:
		oldest_loc = profile.getCurrentPathOldestLocation()
		if(oldest_loc != None):
			purge_to_date = time.time() - config.DAY_IN_SECS

			# Purge everything up to the purge date and dump it into the quadtree.
			while( oldest_loc[1].time < purge_to_date ):
				profile.dumpLocation(oldest_loc)

				oldest_loc = profile.getCurrentPathOldestLocation()	

# We check the distance between our last known coord that is either
# in the current path or last entry into the tree, against our friend's
# profile. If we're within friend range, we artificially set the defcon
# to 0. This does not change the danger level or deviation associated
# with each entry into the current path.
def friendCheck( profile, friend_profile ):

	size_cur_path = len(profile.current_path)
	size_cur_friend_path = len(profile.current_path)

	last_known_coord = None
	last_known_friend_coord = None

	if(size_cur_path > 0):
		
		last_entry = profile.current_path[size_cur_path]

		last_known_coord = last_entry[0]

	else:
		last_known_coord = profile.getLastCoordInQuadTree()

	if(size_cur_friend_path > 0):

		last_friend_entry = friend_profile.current_path[size_cur_friend_path]

		last_known_friend_coord = last_friend_entry[0]

	else:
		last_known_friend_coord = friend_profile.current_path[size_cur_friend_path]

	if ( (last_known_coord != None) and (last_known_friend_coord != None) ):
		distance = distanceBetweenTwoPoints( last_known_coord,
							last_known_friend_coord )

		if( distance <= profile.getFriendRange() ):

			profile.getFriendRange()

			profile.setCurrentDefconLevel( 0 )

def checkDisconnectStatus( profile ):

	if( profile.getIsTrackingDisconnect() ):
		
		return

	last_connection = profile.getTimeStampOfLastMessage()

	max_time = time.time() - profile.getMaxDisconnectTime()

	if( (max_time > last_connection) ):

		for contact in profile.getDefconContactList():

			if((contact.last_alert_time_stamp + profile.getAlertFrequency()) <= time.time()):

				alert.send_alert( contact.addr, contact.msg )

				contact.last_alert_time_stamp = int( time.time() )

def checkTrackingStatus( profile ):

	if( not profile.getIsTracking() ):
		None

def checkDefconStatus( profile ):
	defcon_contacts = profile.getDefconContactList()

	now = int( time.time() )

	for contact in defcon_contacts:
		# If the defcon level exceeds the user-defined threshold
		# AND
		# the last altert plus freq is less than the present time,
		# Send alert and update time stamp
		if( contact.defcon >= profile.getCurrentDefconLevel() and ((contact.last_alert_time_stamp + profile.getAlertFrequency()) <= now ) ):
			
			alert.send_alert( contact.addr, contact.msg )

			# We've sent an alert to update the time stamp.
			contact.last_alert_time_stamp = int( time.time() )
