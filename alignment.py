# Alignment: where multiple ley lines come together
from collections import defaultdict

class Alignment:
	def __init__(self):
		self.alignments = defaultdict(list)
		self.min_key = None
		self.max_key = None

	def getAlignment(self, key):
		if key in self.alignments:
			return self.alignments.get(key)
		else:
			return None

	def addAlignment(self, key, megalith):
		if megalith not in self.alignments.get(key):
			if( key >= self.min_key and key <= self.max_key ):
				self.alignments.get(key).append(megalith)
			else:
				return -1
		else:
			None
			# Probably update preexisting megalith

class Megalith:
	def __init__(self):
		self.quad = None
