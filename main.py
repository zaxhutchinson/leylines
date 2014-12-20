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
from collections import deque

class Leylines:
	def __init__(self):
		
		print("LEYLINES: initiated")
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

		self.loadUIDList()
		self.loadAllProfiles()

		# Holds all the pref_key files needing to be read.
		self.dispatch_queue = Queue.Queue()

		if not os.path.exists(config.LOG_DIR):
			os.makedirs(config.LOG_DIR)

		# Open a log file for errors, etc.
		self.log_file = open( (config.LOG_DIR + '/leylines_' + str(int(time.time())) + '.log'), 'w')
		self.log("LEYLINES LOG FILE: " + str(time.time()) + "\n")

		
		self.stopListening = False
		self.stopMessaging = False
		self.stopDispatching = False
		self.stopRunning = False

		self.open_connections = deque()

		# Socket
		self.leysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#self.leysocket.setblocking(1) # Set to blocking
		self.leysocket.settimeout(1) # Block for one sec
		self.leysocket.bind((config.HOST,config.PORT))
		self.leysocket.listen(100)

		print("LEYLINES: listening on port " + str(config.PORT))

		self.start()

	def __del__(self):
		
		self.storeUIDList()

		for uid in self.loaded_profiles.keys():
			self.storeProfile(uid)

		# Also should check queues for unprocessed messages

		self.log_file.close()

		#self.isRunning = False

	def loadAllProfiles(self):
		for uid in self.all_known_uids:

			self.loadProfile(uid)

	def loadProfile(self, uid):
		profile = None
		try:
			profile = ley_profile.Profile.load(uid)
		except (pickle.UnpicklingError):
			print("Unpickling error: " + str(e))
			return False
		except AttributeError as e:
			print("AttributeError while unpickling: " + str(e))
			return False
		except (EOFError):
			print("EOFError while unpickling: " + str(e))
			return False
		except (ImportError):
			print("ImportError while unpickling: " + str(e))
			return False
		except (IndexError):
			print("IndexError while unpickling: " + str(e))
			return False
		else:
			# In case a profile was stored mid-operation, or something
			# previously went awry, load profile unlocked.
			profile.unlock()

			print(profile.tree_as_list[0])
			# Initialize a new tree with the original first coordinate
			profile.tree = quadtree.QuadTree( profile.tree_as_list[0][0], profile.tree_as_list[0][1] )

			# with all other Coords, rebuild tree
			profile.rebuildTree(profile.tree_as_list)

			self.loaded_profiles_uid_queue.append(uid)
			self.loaded_profiles[uid] = profile
			return True

	def storeProfile(self, uid):
		if( uid in self.loaded_profiles ):

			try:
				self.loaded_profiles[uid].save()
			except(pickle.PicklingError):
				print("ERROR: pickling the uid: " + uid)
				return False
			else:
				#self.loaded_profiles_uid_queue.remove(uid)
				#del self.loaded_profiles[uid]
				return True

	def getProfile(self, uid):
		if( uid in self.loaded_profiles.keys() ):
			print("PROFILE ALREADY LOADED")
			return self.loaded_profiles[uid]
		elif( (uid in self.all_known_uids) and (uid not in self.loaded_profiles.keys()) ):
			if( (self.loadProfile()) == True ):
				print("PROFILE NOT IN MEMORY, LOADING FIRST")
				return self.loaded_profiles[uid]
			else:
				raise
		else:
			return None

	def loadUIDList(self):
		if(os.path.isfile('uid_list')):
			f = open('uid_list','r')

			for uid in f:
				self.all_known_uids.append(uid.strip())
				print(uid.strip())

			f.close()

	def storeUIDList(self):
		f = open('uid_list','w')

		for uid in self.all_known_uids:
			f.write(uid + '\n')

		f.close()

	def start(self):

		print("LEYLINES: starting")

		self.listenManager = threading.Thread(target=self.listenManager)
		self.listenManager.start()

		print("LEYLINES: listenManger started")

		self.messenger = threading.Thread(target=self.messageManager)
		self.messenger.start()

		print("LEYLINES: messenger started")

		self.dispatcher = threading.Thread(target=self.dispatcher)
		self.dispatcher.start()

		print("LEYLINES: dispatcher started")

		try:
			self.run()
		except(KeyboardInterrupt, SystemExit):
			self.stop()
			raise

	def stop(self):
		print("LEYLINES: stopping")

		self.stopListening = True

	def run(self):
		print("LEYLINES: running")
		while( (not self.stopRunning) or (threading.activeCount() > 1) ):

			time.sleep(1)

			#print("SIZE UID QUEUE: " + str(len(self.loaded_profiles_uid_queue)))
			# Do nothing unless there are loaded profiles.
			if( len(self.loaded_profiles_uid_queue) > 0 ):
			
				# Get the uid of the next profile in line
				next_uid = self.loaded_profiles_uid_queue.popleft()

				# Use the uid to retrieve the actual profile
				next_profile = self.loaded_profiles[next_uid]

				# If this profile has been updated
				if next_profile.updated:

					#print("LEYLINES: updating profile " + next_uid)

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

					#print("LEYLINES: profile " + next_uid + " updated")

				# Add the uid to the end of the queue
				self.loaded_profiles_uid_queue.append( next_uid )

			else:
				# No loaded profiles so sleep for a sec
				time.sleep(1)

		print("LEYLINES: saving uid list")
		self.storeUIDList()

		print("LEYLINES: saving profiles")
		for uid in self.loaded_profiles.keys():
			self.storeProfile(uid)

		self.loaded_profiles.clear()
		self.loaded_profiles_uid_queue.clear()

		print("LEYLINES: closing log file")
		# Also should check queues for unprocessed messages
		self.log_file.close()



		print("LEYLINES: offline")
		print("")
		print("######################")
		print("# YOU'RE ON YOUR OWN #")
		print("######################")


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
				print("LEYLINES: connection open to " + str(addr))
				self.open_connections.append((conn,addr))

		self.leysocket.close()
		print("LEYLINES: stopped listening")
		self.stopMessaging = True

	def messageManager(self):
		while( (not self.stopMessaging) or ( len(self.open_connections) > 0 ) ):
			if( len(self.open_connections) > 0 ):
				conn,addr = self.open_connections.popleft()
				print("LEYLINES: handling connection " + str(addr))
				msg = ""
				while(True):
					print("LEYLINES: passing message")
					try:
						data = conn.recv(1024, socket.MSG_DONTWAIT)
						if data:
							msg += data
						else:
							break
					except(socket.timeout, socket.error):
						print("LEYLINES: breaking 0")
						break
					else:
						if len(msg) == 0:
							print("LEYLINES: breaking 1")
							conn.sendall("KO")
							break
				if(len(msg) > 0):		
					print('LEYLINES: msg received')
					conn.sendall('OK')
					self.dispatch_queue.put( (conn,addr,msg),False )
					self.dispatch_queue.task_done()
			time.sleep(1)

		print("LEYLINES: stopped passing messages")
		self.stopDispatching = True
	
	def dispatcher(self):
		#print("DIS START")
		
		# The dispatcher should continue to run until it has been asked
		# to terminate and the dispatch is not empty. It must continue
		# until all messages are processed.
		while( (not self.stopDispatching) or (not self.dispatch_queue.empty()) ):
			if(self.stopDispatching):
				print(self.dispatch_queue.empty())
			msg = None
			try:
				msg = self.dispatch_queue.get(False)
				#self.dispatch_queue.task_done()
			except (Queue.Empty):
				None
			if( msg != None ):
				print("LEYLINES: dispatching message")

				#self.dispatch_queue.task_done()
				conn = msg[0]
				addr = msg[1]
				typ_msg = msg[2].split('\n',1)
				typ = typ_msg[0]
				msg = typ_msg[1]
				
				if( typ == config.MSG_INIT ):
					print("LEYLINES: init msg received")
					init = threading.Thread(target=self.rec_init(msg,conn,addr))
					init.start()
				elif( typ == config.MSG_TRACK ):
					print("LEYLINES: track msg received")
					track = threading.Thread(target=self.rec_track(msg,conn,addr))
					track.start()
				elif( typ == config.MSG_REFRESH ):
					print("LEYLINES: refresh msg received")
					refresh = threading.Thread(target=self.rec_refresh(msg,conn,addr))
					refresh.start()
				elif( typ == config.MSG_LOC ):
					print("LEYLINES: location msg received")
					loc = threading.Thread(target=self.rec_loc(msg,conn,addr))
					loc.start()
				elif( typ == config.MSG_PREF ):
					print("LEYLINES: pref msg received")
					pref = threading.Thread(target=self.rec_pref(msg,conn,addr))
					pref.start()
				elif( typ == config.MSG_POS ):
					print("LEYLINES: position msg received")
					pos = threading.Thread(target = self.rec_pos(msg,conn,addr))
					pos.start()
				elif( typ == config.MSG_DIE ):
					print("LEYLINES: stop msg received")
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
		# terminate
		print("LEYLINES: stopped dispatching")
		self.stopRunning = True

	# The following functions are called by dispatcher depending on
	# the type of message received.

	def rec_init(self, msg, conn, addr):
		print("LEYLINES: processing init profile message")
		items = msg.split('\n')
		userid = items[0]
		info = items[1:]

		if( userid in self.loaded_profiles.keys() ):
			conn.sendall("KO")
			print("LEYLINES: finished init profile message (UID in use)")
			return
		else:
			if( len(info) == 3 ):
				print("LEYLINES: init messsage good")
				coord = misc.GPSCoord( float(info[0]), float(info[1]) )
				data = misc.Data( 0, int(info[2]), 0.0 )
				self.all_known_uids.append(userid)
				self.loaded_profiles[userid] = ley_profile.Profile( userid, coord, data )
				self.loaded_profiles_uid_queue.append(userid)
				print("LEYLINES: sending init response")
				conn.sendall("OK")
				print("LEYLINES: init message sent")

			else:
				conn.sendall("KO")
				return # ERROR, bad initial data

					
	# Searches for a corresponding UID and flips the tracking variable
	# If tracking is turned off, the countdown is initiated. 
	def rec_track(self, msg, conn, addr):
		msg = msg.strip('\n')
		for k,v in self.loaded_profiles.items():
			if (k == msg):
				v.flipisTracking()
				v.setTimeStampOfLastMessage()
				conn.sendall("OK")
				return
		conn.sendall("KO")
		return


		# Will have to return an OK here eventually.
		
	# Should return the status of the user who queried it.
	def rec_refresh(self, msg, conn, addr):
		msg.rstrip('\n')
		for k,v in self.loaded_profiles.items():
			if (k == msg[0]):
				stats = v.getCurrentDefconLevel()
				conn.sendall("OK")
				#conn.sendall("Current defcon level is: " + str(str_stats))
				
	
	#Our newest neglected child
	#Should receive latitude, longitude, day of the week, time of arrival and depature
	#and save them into some sort of class or whatever.
	def rec_loc(self, msg, conn, addr):
		conn.sendall("OK")

	def rec_pref(self, msg, conn, addr):
		msg_split = msg.split('/n')
		userid = msg_split[0]
		prefs = msg_split[1:]

		found_uid = False

		for uid,profile in self.loaded_profiles.items():
			if(uid == userid):

				found_uid = True

				contact1 = profile.Contact()
				contact2 = profile.Contact()
				contact3 = profile.Contact()
		
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


				profile.addContactToDefconContactList( contact1 )
				profile.addContactToDefconContactList( contact2 )
				profile.addContactToDefconContactList( contact3 )
					
				# We found the user's profile in question
				# so break...no need to check the rest.
				if found_uid:
					break;

		if not found_uid:
			conn.sendall("KO")
		else:
			conn.sendall("OK")				
			
	def rec_pos(self, msg, conn, addr):
		print("LEYLINES: processing position message")
		msg_split = msg.split('\n')
		userid = msg_split[0].strip()
		items = msg_split[1:]

		found_uid = False
		profile = self.getProfile(userid)

		if( profile != None ):
			new_lat = 0.0
			new_long = 0.0
			new_time = 0.0
			count = 0
			for line in items:
				if( count == 0 ):
					new_lat = float( line )
					count += 1
				elif( count == 1):
					new_long = float( line )
					count += 1
				elif( count == 2):
					new_time = int( line )
					count += 1

				if( count == 3 ):
					#print("ADDED COORDS: " + str(new_lat) + " " + str(new_long))
					coord = misc.GPSCoord( new_lat, new_long )
					data = misc.Data( profile.getNextDataID(), new_time, 0.0 )
					count = 0

					profile.addNewUnexaminedLocation( coord, data )
		print("LEYLINES: finished position message")


	def log(self, text):
		self.log_file.write(text)


if __name__ == "__main__":
	sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
	l = None
	try:
		l = Leylines()
		#l.start()
	except (KeyboardInterrupt, SystemExit):
		if( l != None ):
			l.stop()
		raise
