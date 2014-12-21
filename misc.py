#############################################################
# misc.py
#
# Data
# What gets stored in the quad tree. It stores a link to and
# from each data node added to the tree before and after it.
# So that paths can be retraced. It also stores a reference in
# the location variable to its parent, so we can get a location.
#
# GPSCoord
# Struct equivalent of lat and long gps coordinates.
# Used all over the place in leylines.
#
#############################################################

class Data:
	def __init__(self, dataID, time, deviation):
		self.dataID = dataID
		self.time = time
		self.deviation = deviation
		self.location = None
		self.prev_entry = None
		self.next_entry = None


class GPSCoord:
	def __init__(self, new_lat, new_long):
		self.latitude = new_lat
		self.longitude = new_long
	def display(self):
		print 'LAT: {}, LONG: {}'.format(self.latitude, self.longitude)


