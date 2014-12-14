import quadtree
import profile
import analyzer
import pickle
import time
import socket
import config
from collections import deque

class Leylines:
	def __init__(self):

		# Holds the profiles currently loaded in a dictionary
		# Key = uid, value is the profile
		self.loaded_profiles = {}
		# This contains the loaded profiles UIDs. The run method
		# cycles through these in order and retrieves them from the
		# sister dictionary above.
		self.loaded_profiles_uid_queue = deque()

		# Holds all the pref_key files needing to be read.
		self.dispatch_queue = Queue.Queue()

		# Open a log file for errors, etc.
		self.log_file = open( ('leylines_' + time.time() + '.log'), 'w')

		# Socket
		self.leysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.leysocket.bind((config.HOST,config.PORT))
		self.leysocket.listen(100)

		self.isRunning = True
		self.isDone = False

		self.start()

	def __del__(self):
		
		for uid in self.loaded_profiles.keys():
			self.storeProfile(uid)

		# Also should check queues for unprocessed messages

		self.log_file.close()

	def loadProfile(self, uid):
		profile = None
		try:
			profile = quadtree.Profile.load(uid)
		except (pickle.UnpicklingError, AttributeError, EOFError, ImportError, IndexError):
			print("ERROR: unpickling the uid: " + uid)
			return False
		else:
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
				del self.loaded_profiles[uid]
				return True

	def start(self):

		self.listener = threading.Thread(target=self.listener)
		self.listener.start()

		self.dispatcher = threading.Thread(target=self.dispatcher)
		self.dispatcher.start()

		self.run()

	def run(self):
		
		while(not self.isDone):
			
			# Get the uid of the next profile in line
			next_uid = self.loaded_profiles_uid_queue.popleft()

			# Use the uid to retrieve the actual profile
			next_profile = self.loaded_profiles[next_uid]

			# If this profile has been updated
			if next_profile.updated:

				# Examine any new locations that have been added
				analyzer.examineNewLocation( next_profile )

				# Examine the current path
				analyzer.examineCurrentPath( next_profile )

				# Check friend levels
				for friend in next_profile.friend_list:


				# If needed, purge all or path of the current path
				# to the quad tree.
				purgeCurrentPathToTree( next_profile )

			# Add the uid to the end of the queue
			self.loaded_profiles_uid_queue.append( next_uid )


		while( threading.activeCount > 1 ):
			# We wait for the other threads handling messages
			# to finish. Sleep for a sec, check again.
			time.sleep(1)

		# Everything is stopped. No, new information coming in.
		# Save all profiles.
		for uid in self.loaded_profiles.keys():
			self.storeProfile(uid)

		# Also should check queues for unprocessed messages
		self.log_file.close()

	def listenManager(self):
		while(isRunning):
			conn,addr = self.leysocket.accept()

			conn_thread = threading.Thread(target=self.listener(conn,addr))
			conn_thread.start()

	def listener(self,conn,addr):
		msg = ""
		while(True):
			data = conn.recv(1024)
			if not data:
				break
			else:
				msg += data
		
		if(len(msg) > 0):
			conn.sendall('OK')
			self.dispatch_queue.put( (conn,addr,msg) )
			self.dispatch_queue.task_done()
		else:
			conn.sendall('KO')
	
	def dispatcher(self):
		
		# The dispatcher should continue to run until it has been asked
		# to terminate and the dispatch is not empty. It must continue
		# until all messages are processed.
		while(isRunning or (not self.dispatch_queue.empty()) ):
			msg = self.dispatch_queue.get()
			self.dispatch_queue.task_done()
			conn = msg[0]
			addr = msg[1]
			typ_msg = msg[2].split('\n',1)
			typ = typ_msg[0]
			msg = typ_msg[1]
			
			if( typ = config.MSG_INIT ):
				init = threading.Thread(target=self.rec_init(msg,conn,addr))
				init.start()
			elif( typ == config.MSG_TRACK ):
				track = threading.Thread(target=self.rec_track(msg,conn,addr))
				track.start()
			elif( typ == config.MSG_REFRESH ):
				refresh = threading.Thread(target=self.rec_refresh(msg,conn,addr))
				refresh.start()
			elif( typ == config.MSG_LOC ):
				loc = threading.Thread(target=self.rec_loc(msg,conn,addr))
				loc.start()
			elif( typ == config.MSG_PREF ):
				pref = threading.Thread(target=self.rec_pref(msg,conn,addr))
				pref.start()
			elif( typ == config.MSG_POS ):
				pos = threading.Thread(target = self.rec_pos(msg,conn,addr))
				pos.start()
			else:
				None # ERROR

		# The dispatcher has processed all messages and is ready to
		# terminate
		self.isDone = True
			

	# The following functions are called by dispatcher depending on
	# the type of message received.

	def rec_init(self, msg, conn, addr):
		items = msg.split('\n')
		userid = items[0]
		info = items[1:]

		if( k in self.loaded_profiles.keys() ):
			conn.sendall("KO")
			return -1
		else:
			if( len(info) == 3 ):
				coord = misc.GPSCoord( float(info[0]), float(info[1]) )
				data = misc.Data( int(info[2]), 0.0 )
				self.loaded_profiles[userid] = profile.Profile( userid, coord, data )
				conn.sendall("OK")
			else:
				conn.sendall("KO")
				return -2 # ERROR, bad initial data

					
	# Searches for a corresponding UID and flips the tracking variable
	# If tracking is turned off, the countdown is initiated. 
	def rec_track(self, msg, conn, addr):
		msg = msg.strip('\n')
		for k,v in self.loaded_profiles.items():
			if (k == msg):
				v.profile.flipisTracking()
				conn.sendall("OK")
			else:
				self.log("Error: User ID not found")
				conn.sendall("KO")
				
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
		msg_split = msg.split('/n')
		userid = msg_split[0]
		items = msg_split[1:]

		found_uid = False

		for k,v in self.loaded_profiles.items():
			if( k == userid ):
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
						coord = misc.GPSCoord( new_lat, new_long )
						data = misc.Data( new_time, 0.0 )

						v.addNewUnexaminedLocation( coord, data )


	def make_new_log(self):
		self.log_file.close()

		self.log_file = open( ('leylines_' + time.time() + '.log'), 'w')

	def log(self, text):
		self.log_file.write(text)

	def stopLeylines(self):
		self.isRunning = False


if __name__ == "__main__"():
	l = Leylines()
	l.start()
