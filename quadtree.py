# QUAD TREE version 1.0
import math
import pickle
import sys
import alignment

MINUTES_TO_METERS = 1852.0
DEGREES_TO_MINUTES = 60.0
EARTH_RADIUS = 6371000
QUAD_DIAMETER = 2**16
QUAD_RADIUS = 2**15
QUAD_MIN = 2**5
PI = 3.14159265358979323846264338327

class Profile:
	def __init__(self, uid, first_name, last_name, coord, data):
		self.uid = uid
		self.first_name = first_name
		self.last_name = last_name
		self.trees = QuadTree(coord, data)

		self.day_dodem = alignment.Alignment()
		self.time_dodem = alignment.Alignment()

	@classmethod
	def load(cls, filename):
		input_file = open(filename, 'rb')
		return pickle.load(input_file)

	def save(self):
		output_file = open(self.uid, 'wb')
		pickle.dump(self, output_file)
		output_file.close()

class Data:
	def __init__(self, new_info):
		self.info = new_info
		self.location = None
		self.prev_entry = None
		self.next_entry = None


class GPSCoord:
	def __init__(self, new_lat, new_long):
		self.latitude = new_lat
		self.longitude = new_long
	def display(self):
		print 'LAT: {}, LONG: {}'.format(self.latitude, self.longitude)

class Quad:
	def __init__(self, parent, top_left, bottom_right):
		self.parent = parent
		self.top_left = top_left
		self.bottom_right = bottom_right

		self.ne = None
		self.se = None
		self.sw = None
		self.nw = None

		self.data = []


class QuadTree:
	def __init__(self, coord, data = None):
		self.prev_entry = None
		self.next_tree = None
		
		top_left = self.getNewTopLeft( coord, QUAD_RADIUS )
		bottom_right = self.getNewBottomRight( coord, QUAD_RADIUS )

		self.root = Quad( None, top_left, bottom_right )

		# DEBUG CODE #
		# self.root.top_left.display()
		# self.root.bottom_right.display()
		##############

		result = self.addCoord( coord, self.root, QUAD_RADIUS, data )

		if( result != 0 ):
			print 'ERROR: creating quad tree. Exiting.'
			sys.exit(1)

		return

	def addData(self, quad, data):
		quad.data.append(data)
		return

	def updateQuadTree( self, new_coord, data ):
		
		tree = self

		while( self.addCoord( new_coord, tree.root, QUAD_RADIUS, data ) != 0 ):
			if( tree.next_tree == None ):
				tree.next_tree = QuadTree( new_coord, data )
			else:
				tree = tree.next_tree

	def addCoord(self, coord, quad, radius, data):

		if(radius <= QUAD_MIN):
			if(data != None):
				data.location = quad
				data.prev_entry = self.prev_entry
			if(self.prev_entry != None):
				self.prev_entry.next_entry = data
			self.prev_entry = data
			self.addData( quad, data )
			return 0
		
		which_quad = self.getQuadForGPSCoord( coord, quad.top_left, quad.bottom_right )
		mid_point = self.getMidPoint( quad.top_left, quad.bottom_right )

		# MAJOR ERROR
		if( which_quad == -2 ):
			print 'ERROR: Coord no longer in quad tree bounds. Exiting\n'
			sys.exit(1)
		# NOT IN QUAD
		elif( which_quad == -1 ):
			return -1
		# NE
		elif( which_quad == 1 ):
			if( quad.ne == None ):
				quad.ne = Quad( quad, 
							GPSCoord(quad.top_left.latitude, mid_point.longitude),
							GPSCoord(mid_point.latitude, quad.bottom_right.longitude) )
			return self.addCoord( coord, quad.ne, (radius / 2), data)
		# SE
		elif( which_quad == 2 ):
			if( quad.se == None ):
				quad.se = Quad( quad, mid_point, quad.bottom_right )
			return self.addCoord( coord, quad.se, (radius / 2), data )
		# SW
		elif( which_quad == 3 ):
			if( quad.sw == None ):
				quad.sw = Quad( quad,
							GPSCoord(mid_point.latitude, quad.top_left.longitude),
							GPSCoord(quad.bottom_right.latitude, mid_point.longitude) )
			return self.addCoord( coord, quad.sw, (radius / 2), data )
		# NW
		elif( which_quad == 4 ):
			if( quad.nw == None ):
				quad.nw = Quad( quad, quad.top_left, mid_point )
			return self.addCoord( coord, quad.nw, (radius / 2), data )			

	def toDegrees( self, radians ):
		return radians * 180.0 / PI

	def toRadians( self, degrees ):
		return degrees * PI / 180.0

	def distanceBetweenTwoPoints( self, GPSone, GPStwo ):
		lat1 = self.toRadians(GPSone.latitude)
		lat2 = self.toRadians(GPStwo.latitude)
		long1 = self.toRadians(GPSone.longitude)
		long2 = self.toRadians(GPStwo.longitude)

		delta_lat = (lat2 - lat1)
		delta_long = (long2 - long1)

		alpha = math.pow(math.sin(delta_lat / 2.0), 2.0) + \
					math.cos(lat1) * math.cos(lat2) + \
					math.pow(math.sin(delta_long / 2.0), 2.0)

		beta = 2 * math.atan2( math.sqrt(alpha), math.sqrt(1 - alpha) )

		return EARTH_RADIUS * beta

	def getGPSCoordByDirectionAndCourse( self, coord, distance, course ):
		course_in_radians = math.radians( course )
		distance_in_radians = math.radians( distance / MINUTES_TO_METERS /
												DEGREES_TO_MINUTES )

		lat1 = math.radians( coord.latitude )
		long1 = math.radians( coord.longitude )

		new_lat = math.asin( math.sin(lat1) * math.cos(distance_in_radians) +
							math.cos(lat1) * math.sin(distance_in_radians) *
							math.cos(course_in_radians) )
		temp_long = math.atan2( math.sin(course_in_radians) * math.sin(distance_in_radians) *
								math.cos(lat1),
								math.cos(distance_in_radians) -
								math.sin(lat1) * math.sin(new_lat) )
		new_long = math.fmod( (long1 + temp_long + PI), (2.0 * PI) )- PI
		
		return GPSCoord( math.degrees(new_lat), math.degrees(new_long) )

	def getNewTopLeft( self, coord, radius ):
		new_top = self.getGPSCoordByDirectionAndCourse( coord, radius, 0.0 )
		new_left = self.getGPSCoordByDirectionAndCourse( coord, radius, 270.0 )

		return GPSCoord(new_top.latitude, new_left.longitude)

	def getNewBottomRight( self, coord, radius ):
		new_bottom = self.getGPSCoordByDirectionAndCourse( coord, radius, 180.0 )
		new_right = self.getGPSCoordByDirectionAndCourse( coord, radius, 90.0 )

		return GPSCoord( new_bottom.latitude, new_right.longitude )

	def getMidPoint( self, top_left, bottom_right ):
		mid_lat = ( (top_left.latitude - bottom_right.latitude) / 2.0 ) + \
					bottom_right.latitude
		mid_long = ( (bottom_right.longitude - top_left.longitude) / 2.0) + \
					top_left.longitude

		return GPSCoord( mid_lat, mid_long )

	def getQuadForGPSCoord( self, coord, top_left, bottom_right ):
		mid_point = self.getMidPoint( top_left, bottom_right )

		# NOT IN THIS QUAD, ERROR
		if( coord.latitude > top_left.latitude or
			coord.latitude <= bottom_right.latitude or
			coord.longitude < top_left.longitude or
			coord.longitude >= bottom_right.longitude ):
			return -1

		# NE
		if( coord.latitude > mid_point.latitude and
			coord.longitude >= mid_point.longitude ):
			return 1
		# SE
		elif( coord.latitude <= mid_point.latitude and
			  coord.longitude >= mid_point.longitude ):
			  return 2
		# SW
		elif( coord.latitude <= mid_point.latitude and
			  coord.longitude < mid_point.longitude ):
			  return 3
		# NW
		elif( coord.latitude > mid_point.latitude and
			  coord.longitude < mid_point.longitude ):
			  return 4
		# ERROR
		else:
			return -2

	def printTree( self, root, level=0 ):
		if(root != None):
			
			print "LEVEL: {}".format(level)

			root.top_left.display()
			root.bottom_right.display()
			if root.data:
				for d in root.data:
					print "DATA: {}".format(d.info)

			self.printTree(root.ne, level+1)
			self.printTree(root.se, level+1)
			self.printTree(root.sw, level+1)
			self.printTree(root.nw, level+1)
