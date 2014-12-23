####################################################################
# main.py
#
# Contributors:
#	Zachary Hutchinson
#	Cameron Rivera
#	Travis Geeting
#	Tamel Nash
#
# main.py provides the infrastructure of leylines server through 
# the Leylines class, which handles communication, messages,
# saving and loading profiles.
# 
####################################################################
import quadtree
import ley_profile
import analyzer
import pickle
import time
import socket
import config
import misc
import Queue
import threading
import os
import sys
from ley_debug import Debugger
from collections import deque
####################################################################

# LEYLINES CLASS:
class Leylines:
	def __init__(self):

		# Handles printing of debug msgs if enabled by cmd line.
		self.debugger = Debugger()

		# Handle command line args
		for arg in sys.argv:

			# Enable debug message printing
			if(arg == "-d" or arg == "--debug"):
				self.debugger.makeActive()
		
		self.debugger.debugMsg("LEYLINES: initiated")
		
		# Holds the profiles currently loaded in a dictionary
		# Key = uid, value is the profile
		self.loaded_profiles = {}
		
		# This contains the loaded profiles UIDs. The run method
		# cycles through these in order and retrieves them from the
		# sister dictionary above.
		self.loaded_profiles_uid_queue = deque()

		# Holds all the uids for all profiles, even those that are
		# not presently loaded.		 
		self.all_known_uids = []

		# Load all_known_uids
		self.loadUIDList()

		# Load all profiles found in the UID list.
		# TODO: This function will eventually go away. There is no reason
		#	to load ALL profiles. They will be loaded as clients send new mgs.
		#	The code is present to do it the proper way, but has not been
		#	as thoroughly tested as just loading all.
		self.loadAllProfiles()

		# Holds new messages from clients. An async queue.
		self.dispatch_queue = Queue.Queue()

		# Create the log directory
		if not os.path.exists(config.LOG_DIR):
			os.makedirs(config.LOG_DIR)
		if not os.path.exists(config.PROFILE_DIR):
			os.makedirs(config.PROFILE_DIR)

		# Open a log file for errors, etc.
		self.log_file = open( (config.LOG_DIR + '/leylines_' + str(int(time.time())) + '.log'), 'w')
		self.log("LEYLINES LOG FILE: " + str(time.time()) + "\n")

		# These booleans are used to shut down various threads of the
		# server application in order, so it can collapse gracefully.
		self.stopListening = False
		self.stopMessaging = False
		self.stopDispatching = False
		self.stopRunning = False

		# Holds open connections
		self.open_connections = deque()

		# Socket stuff [Create, set, bind, listen]
		# Backlog of connections set to 100.
		self.leysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.leysocket.settimeout(1) # Block for one sec
		self.leysocket.bind((config.HOST,config.PORT))
		self.leysocket.listen(100)

		self.debugger.debugMsg("LEYLINES: listening on port " + str(config.PORT))

		self.start()

	# Destructor: needs work, but isn't used presently.
	def __del__(self):
		
		#self.storeUIDList()

		#for uid in self.loaded_profiles.keys():
		#	self.storeProfile(uid)

		#self.log_file.close()

		None

	# Loads all profiles found in the all_known_uids list
	def loadAllProfiles(self):
		for uid in self.all_known_uids:

			self.loadProfile(uid)

	# Loads an individual profile from disk
	def loadProfile(self, uid):

		# Attempt to unpickle the profile
		profile = None
		try:
			profile = ley_profile.Profile.load(uid)
		except (pickle.UnpicklingError):
			self.debugger.debugMsg("Unpickling error: " + str(e))
			return False
		except AttributeError as e:
			self.debugger.debugMsg("AttributeError while unpickling: " + str(e))
			return False
		except (EOFError):
			self.debugger.debugMsg("EOFError while unpickling: " + str(e))
			return False
		except (ImportError):
			self.debugger.debugMsg("ImportError while unpickling: " + str(e))
			return False
		except (IndexError):
			self.debugger.debugMsg("IndexError while unpickling: " + str(e))
			return False
		else:
			# In case a profile was stored mid-operation, or something
			# previous went awry, unlock profile.
			profile.unlock()

			# Initialize a new tree with the original first coordinate
			profile.tree = quadtree.QuadTree( profile.tree_as_list[0][0], profile.tree_as_list[0][1] )

			# Rebuild the quad tree
			profile.rebuildTree(profile.tree_as_list)

			# Profile is loaded, add uid to active queue
			# and store in loaded_profiles
			self.loaded_profiles_uid_queue.append(uid)
			self.loaded_profiles[uid] = profile

			# Successful finish
			return True

	# Saves an individual profile to disk
	def storeProfile(self, uid):
		if( uid in self.loaded_profiles ):

			# Pickle profile
			try:
				self.loaded_profiles[uid].save()
			except(pickle.PicklingError):
				self.debugger.debugMsg("ERROR: pickling the uid: " + uid)
				return False
			else:
				return True

	# Retrieve a profile from the dictionary of loaded_profiles
	# There are three cases: exists and loaded, exists not loaded, does not exist.
	def getProfile(self, uid):
		if( uid in self.loaded_profiles.keys() ):
			self.debugger.debugMsg("LEYLINES: Profile exists, active")
			return self.loaded_profiles[uid]
		elif( (uid in self.all_known_uids) and (uid not in self.loaded_profiles.keys()) ):
			if( (self.loadProfile()) == True ):
				self.debugger.debugMsg("LEYLINES: Profile exists, not loaded")
				return self.loaded_profiles[uid]
			else:
				raise
		else:
			return None

	# Retrieve the list of all uids from disk and load.
	def loadUIDList(self):
		if(os.path.isfile(config.PROFILE_DIR + '/uid_list')):
			f = open(config.PROFILE_DIR + '/uid_list','r')

			for uid in f:
				self.all_known_uids.append(uid.strip())
				print(uid.strip())

			f.close()

	# Write all uids to disk
	def storeUIDList(self):
		f = open(config.PROFILE_DIR + '/uid_list','w')

		for uid in self.all_known_uids:
			f.write(uid + '\n')

		f.close()

	# Start Leylines, called by the Leylines class constructor
	# Starts the three main threads handling communication and
	# message dispatching.
	def start(self):

		self.debugger.debugMsg("LEYLINES: starting")

		self.listenManager = threading.Thread(target=self.listenManager)
		self.listenManager.start()
		self.debugger.debugMsg("LEYLINES: listenManger started")

		self.messenger = threading.Thread(target=self.messageManager)
		self.messenger.start()
		self.debugger.debugMsg("LEYLINES: messenger started")

		self.dispatcher = threading.Thread(target=self.dispatcher)
		self.dispatcher.start()
		self.debugger.debugMsg("LEYLINES: dispatcher started")

		try:
			self.run()
		except(KeyboardInterrupt, SystemExit):
			self.stop()
			raise

	# This function starts the cascade that eventually halts all
	# of Leylines. Process by which this happens is:
	#	- stop listening, so no new connections are made
	#	- stop handling messages, but handle all open connections
	#	- stop dispatching, but dispatch all recv'd messages
	#	- stop running, but make sure all threads handling msgs are done.
	#	- store everything and shut down.
	def stop(self):
		self.debugger.debugMsg("LEYLINES: stopping")

		self.stopListening = True

	# Run - the main loop of leylines.
	# If any profiles are loaded, pull them off the queue, if they have been updated
	# use the analyzer to process new information, and put them back on the queue.
	def run(self):

		self.debugger.debugMsg("LEYLINES: running")
		
		while( (not self.stopRunning) or (threading.activeCount() > 1) ):

			# Do nothing unless there are loaded profiles.
			if( len(self.loaded_profiles_uid_queue) > 0 ):
			
				# Get the uid of the next profile in line
				next_uid = self.loaded_profiles_uid_queue.popleft()

				# Use the uid to retrieve the actual profile
				next_profile = self.loaded_profiles[next_uid]

				# If this profile has been updated
				if next_profile.updated:

					self.debugger.debugMsg("LEYLINES: updating profile " + next_uid)

					# Examine any new locations that have been added
					analyzer.examineNewLocation( next_profile, self.log_file )

					# Examine the current path
					analyzer.examineCurrentPath( next_profile, self.log_file )

					# Check friend levels
					for friend in next_profile.getFriendList():
						None

					# If needed, purge all or path of the current path
					# to the quad tree.
					analyzer.purgeCurrentPathToTree( next_profile )

				# Add the uid to the end of the queue
				self.loaded_profiles_uid_queue.append( next_uid )

			else:
				# No loaded profiles so sleep for a sec
				time.sleep(1)

		# Store list of all uids
		self.debugger.debugMsg("LEYLINES: saving uid list")
		self.storeUIDList()

		# Store all loaded profiles
		self.debugger.debugMsg("LEYLINES: saving profiles")
		for uid in self.loaded_profiles.keys():
			self.storeProfile(uid)

		# Clear out the deques
		self.loaded_profiles.clear()
		self.loaded_profiles_uid_queue.clear()

		# Close the log file
		self.debugger.debugMsg("LEYLINES: closing log file")
		self.log_file.close()

		# We're done...
		self.debugger.debugMsg("LEYLINES: offline")
		self.debugger.debugMsg("")
		self.debugger.debugMsg("######################")
		self.debugger.debugMsg("# YOU'RE ON YOUR OWN #")
		self.debugger.debugMsg("######################")

	# Listen Manager:
	# Runs in a thread all its own, listening for new connections,
	# once made, they are added to the open_connection queue
	def listenManager(self):

		while(not self.stopListening):
			
			conn = None
			addr = None
			
			try:
				conn,addr = self.leysocket.accept()
			except( socket.timeout ):
				None
			except( KeyboardInterrupt, SystemExit ):
				break
				raise

			if( conn != None and addr != None ):
				self.debugger.debugMsg("LEYLINES: connection open to " + str(addr))
				self.open_connections.append((conn,addr))

		# Done, so close the socket properly and signal for
		# message manager to stop.
		self.leysocket.close()
		self.debugger.debugMsg("LEYLINES: stopped listening")
		self.stopMessaging = True

	# Message Manager:
	# Runs in a thread all its own, pulling new messages from any open connections
	# When a new message is received, they are added to the dispatch queue.
	def messageManager(self):

		while( (not self.stopMessaging) or ( len(self.open_connections) > 0 ) ):
			
			if( len(self.open_connections) > 0 ):

				# Get the next connection from the queue
				conn,addr = self.open_connections.popleft()
				
				self.debugger.debugMsg("LEYLINES: handling connection " + str(addr))
				
				msg = ""

				while(True):
					
					self.debugger.debugMsg("LEYLINES: passing message")
					
					# See if there's a message
					try:
						data = conn.recv(1024, socket.MSG_DONTWAIT)
						if data:
							msg += data
						else:
							break
					except(socket.timeout, socket.error):
						self.debugger.debugMsg("LEYLINES: breaking 0")
						break
					else:
						if len(msg) == 0:
							self.debugger.debugMsg("LEYLINES: breaking 1")
							conn.sendall(config.KO_MSG)
							break

				# If we have a message, package into a triple
				# add to dispatch_queue
				if(len(msg) > 0):		
					self.debugger.debugMsg('LEYLINES: msg received')
					self.dispatch_queue.put( (conn,addr,msg),False )
					self.dispatch_queue.task_done()

			# No open connections right now, so chill.
			time.sleep(1)

		# Message Manager is closed for business,
		# tell dispatcher to stop
		self.debugger.debugMsg("LEYLINES: stopped passing messages")
		self.stopDispatching = True
	
	# Dispatcher:
	# Runs in a thread all its own. Pulls messages off the dispatch queue,
	# determines what type they are, and hands them off to a new thread
	# capable of dealing with that particular type of message.
	def dispatcher(self):
		
		# The dispatcher should continue to run until it has been asked
		# to terminate and the dispatch is not empty. It must continue
		# until all messages are processed.
		while( (not self.stopDispatching) or (not self.dispatch_queue.empty()) ):
			
			msg = None
			
			# Non-blocking get from the message queue
			try:
				msg = self.dispatch_queue.get(False)
				#self.dispatch_queue.task_done()
			except (Queue.Empty):
				None

			# If we found a new message...
			if( msg != None ):
				
				self.debugger.debugMsg("LEYLINES: dispatching message")

				# Unpack message into conn, addr and message, and
				# get the type of the message.
				conn = msg[0]
				addr = msg[1]
				typ_msg = msg[2].split('\n',1)
				typ = typ_msg[0]
				msg = typ_msg[1]
				
				# Switch on the message type, create a new thread and hand over
				# responsibility to the new process.
				if( typ == config.MSG_INIT ):
					self.debugger.debugMsg("LEYLINES: init msg received")
					init = threading.Thread(target=self.rec_init(msg,conn,addr))
					init.start()
				elif( typ == config.MSG_TRACK ):
					self.debugger.debugMsg("LEYLINES: track msg received")
					track = threading.Thread(target=self.rec_track(msg,conn,addr))
					track.start()
				elif( typ == config.MSG_REFRESH ):
					self.debugger.debugMsg("LEYLINES: refresh msg received")
					refresh = threading.Thread(target=self.rec_refresh(msg,conn,addr))
					refresh.start()
				elif( typ == config.MSG_LOC ):
					self.debugger.debugMsg("LEYLINES: location msg received")
					loc = threading.Thread(target=self.rec_loc(msg,conn,addr))
					loc.start()
				elif( typ == config.MSG_PREF ):
					self.debugger.debugMsg("LEYLINES: pref msg received")
					pref = threading.Thread(target=self.rec_pref(msg,conn,addr))
					pref.start()
				elif( typ == config.MSG_POS ):
					self.debugger.debugMsg("LEYLINES: position msg received")
					pos = threading.Thread(target = self.rec_pos(msg,conn,addr))
					pos.start()
				elif( typ == config.MSG_DIE ):
					self.debugger.debugMsg("LEYLINES: stop msg received")
					if(msg.strip() == "IAmCompletelySurroundedByNoBeer"):	
						conn.sendall("STOPPING LEYLINES\n")
						self.stop()
					else:
						conn.sendall("IGNORING STOP COMMAND\n")
				else:
					None # ERROR

			else:
				# There are no messages so sleep for a sec
				time.sleep(1)

		# The dispatcher has processed all messages and is ready to
		# terminate. Signal time to stop running.
		self.debugger.debugMsg("LEYLINES: stopped dispatching")
		self.stopRunning = True

	##################################################################
	# The following functions are called by dispatcher depending on
	# the type of message received.
	##################################################################

	# Initialize profile message
	def rec_init(self, msg, conn, addr):

		self.debugger.debugMsg("LEYLINES: processing init profile message")
		
		# Split the message and extract the userid
		items = msg.split('\n')
		userid = items[0]
		info = items[1:]

		# If the userid exists, we cannot initialize a new one
		if( userid in self.loaded_profiles.keys() ):
			
			conn.sendall(config.KO_MSG)
			
			self.debugger.debugMsg("LEYLINES: finished init profile message (UID in use)")

		# Else, make new profile
		else:
			# Make sure the message is proper length
			if( len(info) == 3 ):

				self.debugger.debugMsg("LEYLINES: init messsage good")
				
				# Extract coordinate and create Data object
				coord = misc.GPSCoord( float(info[0]), float(info[1]) )
				data = misc.Data( 0, int(info[2]), 0.0 )
				
				# Add userid to all known userids
				self.all_known_uids.append(userid)

				# Create a new profile and append userid to loaded list
				self.loaded_profiles[userid] = ley_profile.Profile( userid, coord, data )
				self.loaded_profiles_uid_queue.append(userid)
				
				self.debugger.debugMsg("LEYLINES: sending init response")
				
				# OK msg to client
				conn.sendall(config.OK_MSG)
				
				self.debugger.debugMsg("LEYLINES: init message sent")

			# This is not the message we're looking for, KO
			else:

				conn.sendall(config.KO_MSG)

	# Toggle Tracking message
	# Turns on or off server side tracking
	# Searches for a corresponding UID and flips the tracking variable
	# If tracking is turned off, the countdown is initiated.
	# TODO: Needs to handle the case when a profile exists, but
	#	isn't loaded.
	def rec_track(self, msg, conn, addr):
		
		msg = msg.strip('\n')
		
		# Search all profiles for a matching userid
		for k,v in self.loaded_profiles.items():
			
			if (k == msg):
				
				# We found on, flip tracking
				v.flipIsTracking()

				message = self.constructStatusMsg(v)

				conn.sendall(message)
				
				self.debugger.debugMsg( "LEYLINES: tracking " + str(v.getIsTracking()) + " for profile " + v.getUID() )

				# Update disconnect time stamp
				v.setTimeStampOfLastMessage()
				
				return
		
		# We didn't find the profile, KO
		conn.sendall(config.KO_MSG)		
		return

	def constructStatusMsg(self, profile):
		
		message = ""

		stats = profile.getCurrentDefconLevel()

		if(stats < 3):
			message += "NONE "
		elif(stats < 7):
			message += "MODERATE "
		else:
			message += "HIGH "

		if(profile.getIsTracking()):
			message += "TRUE "
		else:
			message += "FALSE "
		
		# These are not supported presently by client
		message += "NONE FALSE\n"

		return message

		
	# Refresh message
	# Should return the status of the user who queried it.
	# TODO: Needs to handle the case when a profile exists, but
	#	isn't loaded.
	# TODO: Message to phone needs improvement.
	def rec_refresh(self, msg, conn, addr):

		msg.split('\n')

		self.debugger.debugMsg("LEYLINES: refreshing profile " + msg)
		
		# Look for the profile in the loaded list, if we find it
		# construct a message the app expects.
		for k,v in self.loaded_profiles.items():
			
			if (k == msg):

				message = self.constructStatusMsg(v)

				v.setTimeStampOfLastMessage()
				conn.sendall(message)
				#conn.sendall("Current defcon level is: " + str(str_stats))

				self.debugger.debugMsg("LEYLINES: refresh msg " + message)

				return
				

	# Location message:
	# This message allows the user to manually add GPS coordinates into
	# his/her quad tree to prepopulate the data with known locations in order
	# to prime the engine, so to speak. Presently, not implemented.
	def rec_loc(self, msg, conn, addr):
		conn.sendall(config.OK_MSG)

	# Preference Update Message:
	# This updates all the preferences of a user's profile.
	def rec_pref(self, msg, conn, addr):

		# Extract userid from message
		msg_split = msg.split('/n')
		userid = msg_split[0]
		prefs = msg_split[1:]

		found_uid = False

		# Cycle through all profiles, if we find a match,
		# update preferences. NOTE: Preference key-value pairs
		# from the phone come in a random order (quick or android prefs)
		# So we have to handle them as they come.
		for k,v in self.loaded_profiles.items():
			if(uid == userid):

				# We found a profile, we'll break when done updating.
				found_uid = True

				# Update time stamp of profile
				v.setTimeStampOfLastMessage()

				# Contact objects.
				contact1 = profile.Contact()
				contact2 = profile.Contact()
				contact3 = profile.Contact()
		
				# Read and update prefs.
				for p in prefs:
					split_pref = p.split('=')
					k = split_pref[0]
					v = split_pref[1]

					if( k == "pref_key_alert_frequency" ):
						profile.setAlertFrequency( int(v) )
					elif( k == "pref_key_gps_collect_frequency" ):
						profile.setGPSCollectionFrequency( int(v) )
					elif( k == "pref_key_gps_send_frequency" ):
						profile.setGPSSendFrequency( int(v) )
					
					elif( k == "pref_key_distance_deviation_setting"):
						profile.setMaxDistanceToKnownQuad( int(v) )
					elif( k == "pref_key_distance_importance" ):
						profile.setWeightDistanceToKnownQuad( int(v) )

					elif( k == "pref_key_time_deviation_setting" ):
						profile.setMaxTimeOnUnknownPath( int(v) )
					elif( k == "pref_key_time_importance" ):
						profile.setWeightTimeOnUnknownPath( int(v) )

					elif( k == "pref_key_distance_deviation_total_setting" ):
						profile.setMaxDistanceOfUnknownPath( int(v) )
					elif( k == "pref_key_distance_total_importance" ):
						profile.setWeightDistanceOfUnknownPath( int(v) )

					elif( "contact1" in k ):
						if( k == "pref_key_contact1_type_setting" ):
							contact1.typ = v
						elif( k == "pref_key_contact1_info_setting" ):
							contact1.addr = v
						elif( k == "pref_key_contact1_alert_setting" ):
							contact1.defcon = int( v )
					elif( "contact2" in k):
						if( k == "pref_key_contact2_type_setting" ):
							contact2.typ = v
						elif( k == "pref_key_contact2_info_setting" ):
							contact2.addr = v
						elif( k == "pref_key_contact2_alert_setting" ):
							contact2.defcon = int( v )
					elif( "contact3" in k):
						if( k == "pref_key_contact3_type_setting" ):
							contact3.typ = v
						elif( k == "pref_key_contact3_info_setting" ):
							contact3.addr = v
						elif( k == "pref_key_contact3_alert_setting" ):
							contact3.defcon = int( v )

				# Store all the contacts
				profile.addContactToDefconContactList( contact1 )
				profile.addContactToDefconContactList( contact2 )
				profile.addContactToDefconContactList( contact3 )
					
				# We found the user's profile in question
				# so break...no need to check the rest.
				if found_uid:
					break;

		# Send response...
		if not found_uid:
			conn.sendall(config.KO_MSG)
		else:
			conn.sendall(config.OK_MSG)				

	# New position message
	# Work horse of Leylines. Handles new GPS coods and time stamps
	# coming in from the client.
	# TODO: Improve how lat, long, time is transferred. Shaky right now.
	def rec_pos(self, msg, conn, addr):
		
		self.debugger.debugMsg("LEYLINES: processing position message")
		
		# Extract user id
		msg_split = msg.split('\n')
		userid = msg_split[0].strip()
		items = msg_split[1:]

		found_uid = False

		# Find the profile.
		profile = self.getProfile(userid)

		# If the profile find was good....
		if( profile != None ):

			# Update time stamp
			profile.setTimeStampOfLastMessage()
			
			new_lat = 0.0
			new_long = 0.0
			new_time = 0.0
			
			count = 0
			
			# Pull lines off one-by-one. Expecting order to be:
			# LATITUDE
			# LONGITUDE
			# TIMESTAMP (in seconds)
			for line in items:
				if(len(line) == 0):
					continue
				if( count == 0 ):
					new_lat = float( line )
					count += 1
				elif( count == 1):
					new_long = float( line )
					count += 1
				elif( count == 2):
					new_time = int( line )
					count += 1

				# We've got a new set of data, so add to profile's
				# unexamined path and reset counter.
				if( count == 3 ):
					#print("ADDED COORDS: " + str(new_lat) + " " + str(new_long))
					coord = misc.GPSCoord( new_lat, new_long )
					data = misc.Data( profile.getNextDataID(), new_time, 0.0 )
					count = 0

					profile.addNewUnexaminedLocation( coord, data )

		# Send message
		conn.sendall("OK\n")
		
		self.debugger.debugMsg("LEYLINES: finished position message")

	# Sends log text to text file.
	def log(self, text):
		self.log_file.write(text)

# Usual python start...
# Create a new leylines object and let it run...
if __name__ == "__main__":

	sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

	l = None

	try:
		l = Leylines()
	except (KeyboardInterrupt, SystemExit):
		if( l != None ):
			l.stop()
		raise
