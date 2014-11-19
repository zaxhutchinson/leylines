import quadtree
import pickle
import time

class Message:
	def __init__(self, mtype, mdata):
		self.mtype = mtype	# A MSG_XXX type from the config file.
		self.mdata = mdata

class Leylines:
	def __init__(self):

		# Holds the profiles currently loaded in a dictionary
		# Key = uid, value is the profile
		self.loaded_profiles = {}

		# Holds all the pref_key files needing to be read.
		self.dispatch_queue = Queue.Queue()

		self.log_file = open( ('leylines_' + time.time() + '.log'), 'w')

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
		None

	def dispatcher(self):
		
		while(True):
			msg = self.dispatch_queue.get()

			if( msg.mtype == MSG_AWK ):
				self.rec_awk(msg)
			elif( msg.mtype == MSG_DATA ):
				self.rec_data(msg)
			elif( msg.mtype == MSG_PREF ):
				self.rec_pref(msg)
			else:
				None # ERROR
			

	# The following functions are called by dispatcher depending on
	# the type of message received.
	def rec_awk(self, msg):
		None
	
	def rec_data(self, msg):
		None

	def rec_pref(self, msg):
		None


	def make_new_log(self):
		self.log_file.close()

		self.log_file = open( ('leylines_' + time.time() + '.log'), 'w')

	def log(self, text):
		self.log_file.write(text)


if __name__ == "__main__"():
	l = Leylines()
	l.start()
