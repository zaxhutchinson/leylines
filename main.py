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
		self.leysocket = socket.socket(socket.AF.INET, socket.SOCK_STREAM)
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

	def listener(self):
		while(isRunning):
			conn,addr = self.leysocket.accept()
			msg = ""
			while(True):
				data = conn.recv(1024)
				if not data:
					break
				else:
					msg += data
			
			if(len(msg) > 0):
				conn.sendall('OK')
				self.dispatch_queue.put(msg)
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
			typ_msg = msg.split('\n',1)
			typ = typ_msg[0]
			msg = typ_msg[1]
			
			# TO-DO
			# EXTRACT TYPE FROM MESSAGE

			if( typ == config.MSG_TRACK ):
				track = threading.Thread(target=self.rec_track(msg))
				track.start()
			elif( typ == config.MSG_REFRESH ):
				rec_refresh = threading.Thread(target=self.rec_refresh(msg))
				rec_refresh.start()
			elif( typ == config.MSG_LOC ):
				rec_loc = threading.Thread(target=self.rec_loc(msg))
				rec_loc.start()
			elif( typ == config.MSG_PREF ):
				rec_pref = threading.Thread(target=self.rec_pref(msg))
				rec_pref.start()
			elif( typ == config.MSG_POS ):
				rec_pos = threading.Thread(target = self.rec_pos(msg))
				rec_pos.start()
			else:
				None # ERROR

		# The dispatcher has processed all messages and is ready to
		# terminate
		self.isDone = True
			

	# The following functions are called by dispatcher depending on
	# the type of message received.
	
	# Searches for a corresponding UID and flips the tracking variable
	# If tracking is turned off, the countdown is initiated. 
	def rec_track(self, msg):
		msg.rstrip('\n')
		for k,v in self.loaded_profiles.items():
			if (k == msg):
				booo = True
				booo = v.profile.flipisTracking()
				if(not booo):
					#Start the final countdown
				else:
					
			else:
				self.log("Error: User ID not found")
				
		# Will have to return an OK here eventually.
		
	''' Should return the status of the user who queried it.
	def rec_refresh(self, msg):
		msg.rstrip('\n')
		for k,v in self.loaded_profiles.items():
			if (k == msg[0]):
				stats = v.profile.getCurrentDefconLevel()
				str_ stats = str(stats)
				return "Current defcon level is " + str_stats
				
	
	#Our newest neglected child
	#Should receive latitude, longitude, day of the week, time of arrival and depature
	#and save them into some sort of class or whatever.
	def rec_loc(self, msg):
		None
	'''
	def rec_pref(self, msg):
		q = msg[0]
		msg_Mod = msg[1:len(msg)-1].split('\n', -1)
	
		for k,v in self.loaded_profiles.items():
			if(k == q)
			
	def rec_pos(self, msg):
		None

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
