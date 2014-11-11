# Alignment: where multiple ley lines come together
from collections import defaultdict
import datetime
import time

MIN_VISITS_TO_CREATE_MEGALITH = 2

class Dodman:
	def __init__(self):
		self.alignments = defaultdict(list)

	def getAlignment(self, key):
		k = self.parseKey(key)
		if k in self.alignments.keys():
			return self.alignments.get(k)
		else:
			return None
	
	def parseKey(self, key):
		return key
	
	def addQuad(self, key, quad):
		for k,v in self.alignments.items():
			if( v.quad == quad ):
				v.visits += 1
				return True
		self.alignments[self.parseKey(key)] = Megalith(quad)

class TimeDodman(Dodman):
	def __init__(self, time_block):
		Dodman.__init__()
		self.time_block = time_block

	# Conversion helper function: takes a time stamp saved in a quad
	# and returns the hour and minute block in military time.
	# E.G.: 1:31 PM will return 132 if time_block is set to 15 minutes
	#
	def parseKey(self, key):
		dt = datetime.datetime.fromtimestamp(key)
		t = dt.time()
		hour = t.hour * 100
		min_block = int(t.minute / self.time_block)
		return hour + min_block

class DateDodman(Dodman):
	def __init__(self):
		Dodman.__init__()
	
	# Conversion helper: returns day of the week
	# MON: 0, SUN: 6
	def parseKey(self, key):
		dt = datetime.datetime.fromtimestamp(key)
		return dt.weekday()



# NOTE: I think this is a necessary abstraction from simply storing the quad
#	for the reason that a quad can be stored multiple times in an alignment
#	if the key is different.
#
# NOTE: Visits start presently at two because you must visit a quad
#	at least twice with the same key in order for it to be considered
#	an alignment.
class Megalith:
	def __init__(self, quad):
		self.quad = quad
		self.visits = MIN_VISITS_TO_CREATE_MEGALITH
