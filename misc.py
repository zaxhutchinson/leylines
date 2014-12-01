class Data:
	def __init__(self, time, deviation):
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


