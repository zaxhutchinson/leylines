import time
import math
import config
import alert
from collections import deque

def toDegrees( radians ):
	return radians * 180.0 / config.PI

def toRadians( degrees ):
	return degrees * config.PI / 180.0

def distanceBetweenTwoPoints( self, GPSone, GPStwo ):
	lat1 = toRadians(GPSone.latitude)
	lat2 = toRadians(GPStwo.latitude)
	long1 = toRadians(GPSone.longitude)
	long2 = toRadians(GPStwo.longitude)

	delta_lat = (lat2 - lat1)
	delta_long = (long2 - long1)

	alpha = math.pow(math.sin(delta_lat / 2.0), 2.0) + \
				math.cos(lat1) * math.cos(lat2) + \
				math.pow(math.sin(delta_long / 2.0), 2.0)

	beta = 2 * math.atan2( math.sqrt(alpha), math.sqrt(1 - alpha) )

	return config.EARTH_RADIUS * beta

def calculateTimeDeviation( max_time, time ):
	return max_time - time
def calculateRelativeDistanceDeviation( max_dist, dist ):
	return max_dist - dist
def calculateTotalDistanceDeviation( max_dist, dist ):
	return max_dist - dist


# Examines the unexamined_path of the profile and adds it to the
# current_path.
def examineNewLocation( profile ):

	# Since this is a while something loop, we need to have a max number of
	# iterations or else there is a theoretical risk, it never terminates
	# if someone's app continues to update the queue with GPS coords. 
	count = 0

	while( (not profile.unexamined_path.empty()) and count < 10):

		new_loc = profile.unexamined_path.get()
		
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

			# Calculate the relative distance deviation
			raw_deviation_distance_known_location = float(distance_to_known_quad) / 
												float(profile.getMaxDistanceToKnownQuad())

			# Get previous location added to current path
			previous_location = profile.getMostRecentLocationInCurrentPath()
			
			# Calculate and update total distance of this unknown path
			present_dist = profile.getCurrentUnknownDistance() +
							distanceBetweenTwoPoints(new_loc[0], previous_location[0])
			profile.setUnknownDistance(present_dist)

			# Calculate deviation for total distance
			raw_deviation_total_distance = float(present_dist) /
										float(profile.getMaxDistanceOfUnknownPath()

			# Get time on unknown path. In seconds...probably.
			time_on_unknown_path = new_loc[1].time - profile.getCurrentUnknownPathTimeStamp()

			# Calc the time deviation
			raw_deviation_time = float(time_on_unknown_path) /
								float(profile.getMaxTimeOnUnknownPath())

			deviation_relative_distance = raw_deviation_relative_distance *
										profile.getWeightDistanceToKnownQuad()
			deviation_total_distance = raw_deviation_total_distance *
										profile.getWeightDistanceOfUnknownPath()
			deviation_total_time = raw_deviation_time *
								profile.getWeightTimeOnUnknownPath()

			total_weight = profile.getWeightDistanceToKnownQuad() +
						profile.getWeightDistanceOfUnknownPath() +
						profile.getWeightTimeOnUnknownPath()
			
			total_deviation = (deviation_relative_distance +
							deviation_total_distance +
							deviation_time) / total_weight

		profile.appendToCurrentPathFromParts( new_loc[0], new_loc[1], total_deviation )

		# Unlock Queue
		profile.unexamined_path.task_done()

		# Last thing
		count += 1

	if( profile.unexamined_path.empty() ):
		profile.updated = False

# 			
def examineCurrentPath( profile ):

	length = len(profile.current_path)

	if(length > 0):

		# Where we'll store location's when we pull them off the path
		temp_deque = deque()

		# Get the last location we added to the current path
		last_loc = profile.getCurrentPathNewestLocation()
		if(last_loc != None):
			temp_deque.append(last_loc)

			# Get the time in secs of ( last_time - GPS Send Freq )
			max_time = last_loc[1].time - 
				(config.DANGER_LEVEL_TIME_BLOCK * profile.getGPSSendFrequency())

			# Loop while we haven't reached the beginning of the queue
			# and the time of the present element we're inspecting is
			# is not older than max_time
			while( True ):
				#Get next oldest location
				last_loc = profile.getCurrentPathNewestLocation()
					# If it falls within the GPS send time...
					if(last_loc[1].time < max_time):

						# Add it to the temp queue
						temp_deque.append(last_loc)
					
					else:
						profile.appendToCurrentPathFromWhole(last_loc)
						break
		else:
			break
		
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
		if(number_inspected > 0):
			profile.setCurrentDangerLevel( total_deviation / number_inspected )

# Remove older additions from the current path depending on the current defcon level.
def purgeCurrentPathToTree( profile ):

	# If the current defcon level is above the defcon threshold, do not
	# send any data to the quad tree.
	if(profile.getCurrentDefconLevel() <= profile.getAverageDefconThreshold()):
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
			max_purge_to_date = (int(time.time()) - profile.getGPSSendFrenquency() )
			if(purge_to_date > max_purge_to_date ):
				purge_to_date = max_purge_to_date

			# Purge everything up to the purge date and dump it into the quadtree.
			while( oldest_loc[1].time < purge_to_date ):
				profile.dumpLocation(oldest_loc)

				oldest_loc = profile.getCurrentPathOldestLocation()	

		else:
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

		else:
			break

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

	if ( (last_known_coord not None) and (last_known_friend_coord not None) ):
		distance = distanceBetweenTwoPoints( last_known_coord,
							last_known_friend_coord )

		if( distance <= profile.getFriendRange() ):

			profile.getFriendRange()

			profile.setCurrentDefconLevel( 0 )

def checkDisconnectStatus( profile ):
	


def checkTrackingStatus( profile ):

	if( not profile.getIsTracking() ):
		

def checkDefconStatus( profile ):
	defcon_contacts = profile.getDefconContactList()

	now = int( time.time() )

	for contact in defcon_contacts:
		# If the defcon level exceeds the user-defined threshold
		# AND
		# the last altert plus freq is less than the present time,
		# Send alert and update time stamp
		if( contact.defcon >= profile.getCurrentDefconLevel() and
			(contact.last_alert_time_stamp + profile.getAlertFrequency()) <= now ) ):
			
			alert.send_alert( profile.getPassword(), contact.addr, contact.msg )

			# We've sent an alert to update the time stamp.
			contact.last_alert_time_stamp = int( time.time() )
