import quadtree
import profile
import analyzer
import pickle
import time
import socket
import config

class Leylines:
	def __init__(self):

		# Holds the profiles currently loaded in a dictionary
		# Key = uid, value is the profile
		self.loaded_profiles = {}

		# Holds all the pref_key files needing to be read.
		self.dispatch_queue = Queue.Queue()

		# Open a log file for errors, etc.
		self.log_file = open( ('leylines_' + time.time() + '.log'), 'w')

		# Socket
		self.leysocket = socket.socket(socket.AF.INET, socket.SOCK_STREAM)
		self.leysocket.bind((config.HOST,config.PORT))
		self.leysocket.listen(100)


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

		listener = threading.Thread(target=self.listener)
		listener.daemon = True
		listener.start()

		dispatcher = threading.Thread(target=self.dispatcher)
		dispatcher.daemon = True
		dispatcher.start()

	def listener(self):
		while(True):
			conn,addr = self.leysocket.accept()
			msg = ""
			while(True):
				data = conn.recv(1024)
				if not data:
					break
				else:
					msg += data
			
			if(len(msg) > 0):
				self.dispatch_queue.put(msg)
				self.dispatch_queue.task_done()

	def dispatcher(self):
		
		while(True):
			msg = self.dispatch_queue.get()
			self.dispatch_queue.task_done()
			#typ_msg = msg.split('\n',1)
			
			# TO-DO
			# EXTRACT TYPE FROM MESSAGE

			if( typ == config.MSG_AWK ):
				awk = threading.Thread(target=self.rec_awk(msg))
				awk.start()
			elif( typ == config.MSG_INIT ):
				rec_init = threading.Thread(target=self.rec_init(msg))
				rec_init.start()
			elif( typ == config.MSG_PREF ):
				rec_pref = threading.Thread(target=self.rec_pref(msg))
				rec_pref.start()
			elif( typ == config.MSG_GPS ):
				rec_gps = threading.Thread(target=self.rec_gps(msg))
				rec_gps.start()
			else:
				None # ERROR
			

	# The following functions are called by dispatcher depending on
	# the type of message received.
	def rec_awk(self, msg):
		None
	
	def rec_init(self, msg):
		None

	def rec_pref(self, msg):
		None

	def rec_gps(self, msg):
		None


	def make_new_log(self):
		self.log_file.close()

		self.log_file = open( ('leylines_' + time.time() + '.log'), 'w')

	def log(self, text):
		self.log_file.write(text)


if __name__ == "__main__"():
	l = Leylines()
	l.start()
