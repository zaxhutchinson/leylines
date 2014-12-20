# QUAD TREE version 1.0
import math
import pickle
import sys
import time
from collections import deque

import config
import alignment
import misc

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

		self.current_radius_exp = config.RADIUS_EXP

		self.current_radius = self.getCurrentRadiusInQuads()
	
		top_left = self.getNewTopLeft( coord, self.current_radius )
		bottom_right = self.getNewBottomRight( coord, self.current_radius )

		self.root = Quad( None, top_left, bottom_right )

		# 1 = Sunday, 7 = Saturday
		self.dodman_of_day = alignment.DateDodman()
		# Military time: format 0000 = midnight to midnight+time_block
		self.dodman_of_time = alignment.TimeDodman()

		result = self.addCoord( coord, self.root, self.current_radius, data )

		if( result != 0 ):
			print 'ERROR: creating quad tree. Exiting.'
			sys.exit(1)

		return

	def rebuildQuadTree(self, tree_as_dic):

		for i in range(1, len(tree_as_dic)):

			mid_point = tree_as_dic[i][0]

			data = tree_as_dic[i][1]

			if(data.prev_entry is not None):
				data.prev_entry = tree_as_dic[data.prev_entry][1]
			else:
				data.prev_entry = None
			if(data.next_entry is not None):
				data.next_entry = tree_as_dic[data.next_entry][1]
			else:
				data.next_entry = None

			self.addNewData(mid_point, data)
		

	def flattenTree(self):
		extracted_data = []

		sub_list = self.flattenQuadTree(self.root, self.current_radius)

		if( len(sub_list) > 0 ):
			extracted_data.extend(sub_list)

		data_dic = {}

		for data in extracted_data:

			if(data[1].prev_entry is not None):
				data[1].prev_entry = data[1].prev_entry.dataID
			else:
				data[1].prev_entry = None
			if(data[1].next_entry is not None):
				data[1].next_entry = data[1].next_entry.dataID
			else:
				data[1].next_entry = None

			data_dic[data[1].dataID] = data

		return data_dic


	def flattenQuadTree(self, quad, radius):

		extracted_data = []

		if( radius <= config.QUAD_MIN ):
			mid_point = self.getMidPoint(quad.top_left, quad.bottom_right)
			for d in quad.data:
				extracted_data.append( (mid_point, d) )

		else:
			if( quad.ne != None ):
				sub_list = self.flattenQuadTree(quad.ne, (radius / 2))
				if( len(sub_list) > 0 ):
					extracted_data.extend(sub_list)
			if( quad.se != None ):
				sub_list = self.flattenQuadTree(quad.se, (radius / 2))
				if( len(sub_list) > 0 ):
					extracted_data.extend(sub_list)
			if( quad.sw != None ):
				sub_list = self.flattenQuadTree(quad.sw, (radius / 2))
				if( len(sub_list) > 0 ):
					extracted_data.extend(sub_list)
			if( quad.nw != None ):
				sub_list = self.flattenQuadTree(quad.nw, (radius / 2))
				if( len(sub_list) > 0 ):
					extracted_data.extend(sub_list)

		return extracted_data

	def addData(self, quad, data):
		quad.data.append(data)
		if( len(quad.data) >= config.MIN_VISITS_TO_CREATE_MEGALITH ):
			self.dodman_of_time.addQuad(data.time, quad)
			self.dodman_of_day.addQuad(data.time, quad)
		return

	def addNewData(self, coord, data):
		if( (self.addCoord( coord, self.root, self.current_radius, data)) == -2 ):
			return False
		else:
			return True

	def addCoord(self, coord, quad, radius, data):

		if(radius <= config.QUAD_MIN):
			if(data != None):
				data.location = quad
				data.prev_entry = self.prev_entry
			if(self.prev_entry != None):
				self.prev_entry.next_entry = data
			self.prev_entry = data
			self.addData( quad, data )
			return 0
		
		which_quad = self.getRelativeQuadrantForCoord( coord, quad.top_left, quad.bottom_right )
		mid_point = self.getMidPoint( quad.top_left, quad.bottom_right )

		# MAJOR ERROR
		if( which_quad == -2 ):
			return -2	
		# NOT IN QUAD
		elif( which_quad == -1 ):
			if( (self.enlargeQuadTree( coord )) == -2 ):
				return -2
			else:
				return self.addCoord( coord, self.root, self.current_radius, data )
		# NE
		elif( which_quad == 1 ):
			if( quad.ne == None ):
				quad.ne = Quad( quad, 
							misc.GPSCoord(quad.top_left.latitude, mid_point.longitude),
							misc.GPSCoord(mid_point.latitude, quad.bottom_right.longitude) )
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
							misc.GPSCoord(mid_point.latitude, quad.top_left.longitude),
							misc.GPSCoord(quad.bottom_right.latitude, mid_point.longitude) )
			return self.addCoord( coord, quad.sw, (radius / 2), data )
		# NW
		elif( which_quad == 4 ):
			if( quad.nw == None ):
				quad.nw = Quad( quad, quad.top_left, mid_point )
			return self.addCoord( coord, quad.nw, (radius / 2), data )

	def isKnownCoord(self, coord):
		if(self.getLeafQuadForCoord(self.root, self.current_radius, coord) == None):
			return False
		else:
			return True

	def isCoordInLastAddedQuad(self, coord):
		quad = self.getLeafQuadForCoord( self.root, self.current_radius, coord )

		if(quad == self.prev_entry):
			return True
		else:
			return False

	def getLeafQuadForCoord(self, quad, radius, coord):
		if(radius <= config.QUAD_MIN):
			return quad

		which_quad = self.getRelativeQuadrantForCoord( coord, quad.top_left, quad.bottom_right )
		
		if( which_quad == -2 or which_quad == -1 ):
			return None
		elif( which_quad == 1):
			if( quad.ne == None): 
				return None
			else:
				return self.getLeafQuadForCoord(quad.ne, (radius / 2), coord)
		elif( which_quad == 2):
			if( quad.se == None):
				return None
			else:
				return self.getLeafQuadForCoord(quad.se, (radius / 2), coord)
		elif( which_quad == 3):
			if( quad.sw == None):
				return None
			else:
				return self.getLeafQuadForCoord(quad.sw, (radius / 2), coord)
		elif( which_quad == 4):
			if( quad.nw == None ):
				return None
			else:
				return self.getLeafQuadForCoord(quad.nw, (radius / 2), coord)

	def enlargeQuadTree( self, coord ):
		exterior_quadrant = self.getQuadrantForExteriorCoord( coord )

		new_root_top_left = None
		new_root_bottom_right = None

		new_root = None

		self.current_radius_exp += 1

		if(exterior_quadrant == 1):
			new_root_top_left = self.getGPSCoordByDirectionAndCourse( 
				self.root.top_left, self.current_radius, 0 )		
			new_root_bottom_right = self.getGPSCoordByDirectionAndCourse( 
				self.root.bottom_right, self.current_radius, 90 )
			new_root = Quad( None, new_root_top_left, new_root_bottom_right )
			new_root.sw = self.root
		elif(exterior_quadrant == 2):
			new_root_top_left = self.root.top_left
			new_lat = self.getGPSCoordByDirectionAndCourse( 
				self.root.bottom_right, self.current_radius, 90).longitude
			new_long = self.getGPSCoordByDirectionAndCourse( 
				self.root.bottom_right, self.current_radius, 180).latitude
			new_root_bottom_right = GPSCoord( new_lat, new_long )
			new_root = Quad(None, new_root_top_left, new_root_bottom_right )
			new_root.nw = self.root
		elif(exterior_quadrant == 3):
			new_root_top_left = self.getGPSCoordByDirectionAndCourse( 
				self.root.top_left, self.current_radius, 270)
			new_root_bottom_right = self.getGPSCoordByDirectionAndCourse( 
				self.root.bottom_right, self.current_radius, 90)
			new_root = Quad(None, new_root_top_left, new_root_bottom_right )
			new_root.ne = self.root
		elif(exterior_quadrant == 4):
			new_lat = self.getGPSCoordByDirectionAndCourse( 
				self.root.top_left, self.current_radius, 0).latitude
			new_long = self.getGPSCoordByDirectionAndCourse( 
				self.root.top_left, self.current_radius, 270).longitude
			new_root_top_left = GPSCoord( new_lat, new_long )
			new_root_bottom_right = self.root.bottom_right
			new_root = Quad(None, new_root_top_left, new_root_bottom_right )
			new_root.se = self.root
		elif(exterior_quadrant == -1):
			return -2 # MAJOR FUCKING ERROR
		else:
			return -2 # MAJOR FUCKING ERROR

		# Set new root
		self.root = new_root


	def getQuadrantForExteriorCoord( self, coord ):
		midpoint = self.getMidPoint( self.root.top_left, self.root.bottom_right )

		if( coord.latitude > midpoint.latitude and coord.longitude >= midpoint.longitude ):
			return 1
		elif( coord.latitude <= midpoint.latitude and coord.longitude >= midpoint.longitude ):
			return 2
		elif( coord.latitude <= midpoint.latitude and coord.longitude < midpoint.longitude ):
			return 3
		elif( coord.latitude > midpoint.latitude and coord.longitude < midpoint.longitude ):
			return 4
		else:
			return -1

	def toDegrees( self, radians ):
		return radians * 180.0 / config.PI

	def toRadians( self, degrees ):
		return degrees * config.PI / 180.0

	def distanceBetweenTwoPoints( self, GPSone, GPStwo ):
		lat1 = self.toRadians(GPSone.latitude)
		lat2 = self.toRadians(GPStwo.latitude)
		long1 = self.toRadians(GPSone.longitude)
		long2 = self.toRadians(GPStwo.longitude)

		delta_lat = (lat2 - lat1)
		delta_long = (long2 - long1)

		alpha = math.pow(math.sin(delta_lat / 2.0), 2.0) + \
					math.cos(lat1) * math.cos(lat2) * \
					math.pow(math.sin(delta_long / 2.0), 2.0)

		beta = 2 * math.atan2( math.sqrt(alpha), math.sqrt(1 - alpha) )

		return config.EARTH_RADIUS * beta

	def getGPSCoordByDirectionAndCourse( self, coord, distance, course ):
		course_in_radians = math.radians( course )
		#print(distance / config.MINUTES_TO_METERS / config.DEGREES_TO_MINUTES)
		distance_in_radians = math.radians( distance / config.MINUTES_TO_METERS /
												config.DEGREES_TO_MINUTES )

		lat1 = math.radians( coord.latitude )
		long1 = math.radians( coord.longitude )

		new_lat = math.asin( math.sin(lat1) * math.cos(distance_in_radians) +
							math.cos(lat1) * math.sin(distance_in_radians) *
							math.cos(course_in_radians) )
		temp_long = math.atan2( math.sin(course_in_radians) * math.sin(distance_in_radians) *
								math.cos(lat1),
								math.cos(distance_in_radians) -
								math.sin(lat1) * math.sin(new_lat) )
		new_long = math.fmod( (long1 + temp_long + config.PI), (2.0 * config.PI) )- config.PI
		
		return misc.GPSCoord( math.degrees(new_lat), math.degrees(new_long) )

	def getNewTopLeft( self, coord, radius ):
		new_top = self.getGPSCoordByDirectionAndCourse( coord, radius, 0.0 )
		new_left = self.getGPSCoordByDirectionAndCourse( coord, radius, 270.0 )

		return misc.GPSCoord(new_top.latitude, new_left.longitude)

	def getNewBottomRight( self, coord, radius ):
		new_bottom = self.getGPSCoordByDirectionAndCourse( coord, radius, 180.0 )
		new_right = self.getGPSCoordByDirectionAndCourse( coord, radius, 90.0 )

		return misc.GPSCoord( new_bottom.latitude, new_right.longitude )

	def getMidPoint( self, quad ):
		return self.getMidPoint( quad.top_left, quad.bottom_right )

	def getMidPoint( self, top_left, bottom_right ):
		mid_lat = ( (top_left.latitude - bottom_right.latitude) / 2.0 ) + \
					bottom_right.latitude
		mid_long = ( (bottom_right.longitude - top_left.longitude) / 2.0) + \
					top_left.longitude

		return misc.GPSCoord( mid_lat, mid_long )

	def getPrevEntryLocationMidPoint(self):
		prev_quad = self.prev_entry.location

		return self.getMidPoint( prev_quad.top_left, prev_quad.bottom_right )

	def getRadiusOfQuad( self, quad ):
		top_right = misc.GPSCoord( quad.top_left.latitude, quad.bottom_right.longitude )

		return (self.distanceBetweenTwoPoints( quad.top_left, top_right ) / 2.0)

	def getRelativeQuadrantForCoord( self, coord, quad ):
		return getRelativeQuadrantForCoord( coord, quad.top_left, quad.bottom_right )

	def getRelativeQuadrantForCoord( self, coord, top_left, bottom_right ):
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

	def getDistanceToGoodQuad(self, coord):
		closest_good_quad = self.getClosestGoodQuad(coord)
		mid_point = self.getMidPoint(closest_good_quad.top_left,
										closest_good_quad.bottom_right)
		return self.distanceBetweenTwoPoints( mid_point, coord )

	def getClosestGoodQuad(self, coord ):
		
		# The list of current candidates for closest good quad
		open_list = []
		
		# Current closest quad
		closest_quad = None
		closest_quad_dist = None

		# Add the root's children to the open list.
		if( self.root.ne != None ):
			open_list.append(self.root.ne)
		if( self.root.se != None ):
			open_list.append(self.root.se)
		if( self.root.sw != None ):
			open_list.append(self.root.sw)
		if( self.root.nw != None ):
			open_list.append(self.root.nw)

		while( True ):

			for q in open_list:

				q_mid = self.getMidPoint(q.top_left, q.bottom_right)
				q_dist = self.distanceBetweenTwoPoints( q_mid, coord )

				if( closest_quad_dist == None or q_dist < closest_quad_dist ):

					closest_quad = q
					closest_quad_dist = q_dist
				
			# If closest_quad's radius is <= QUAD_MIN, break, we have a leaf-level
			# quad.
			#print("TOP_LEFT:     " + str(closest_quad.top_left.latitude) + " " + str(closest_quad.top_left.longitude))
			#print("BOTTOM_RIGHT: " + str(closest_quad.bottom_right.latitude) + " " + str(closest_quad.bottom_right.longitude))
			#print("RADIUS: " + str(self.getRadiusOfQuad( closest_quad) ))
			if( int(self.getRadiusOfQuad( closest_quad )) <= config.QUAD_MIN ):
				
				break

			# Else add all the closest_quad's children to the open list.
			# And remove the closest quad from the list. 
			else:
				if( closest_quad.ne != None ):
					open_list.append( closest_quad.ne )
				if( closest_quad.se != None ):
					open_list.append( closest_quad.se )
				if( closest_quad.sw != None ):
					open_list.append( closest_quad.sw )
				if( closest_quad.nw != None ):
					open_list.append( closest_quad.nw )

				open_list.remove( closest_quad )
				closest_quad = None
				closest_quad_dist = None


		return closest_quad

	def isPointInTree(self, coord, container_quad):
		
		return self.isPointInTree(coord, self.root, self.current_radius, container_quad)

	def isPointInTree(self, coord, quad, radius):
		subquad = getGPSCoordForCoord(coord, quad)

		if(radius == config.QUAD_MIN):
			container_quad = quad
			return True

		if(subquad == 1):
			if(quad.ne != None):
				isPointInTree(coord, quad.ne, radius / 2, container_quad)
			else:
				return nil
		elif(subquad == 2):
			if(quad.se != None):
				isPointInTree(coord, quad.se, radius / 2, container_quad)
			else:
				return nil
		elif(subquad == 3):
			if(quad.sw != None):
				isPointInTree(coord, quad.sw, radius / 2, container_quad)
			else:
				return nil
		elif(subquad == 4):	
			if(quad.nw != None):
				isPointInTree(coord, quad.nw, radius / 2, container_quad)
			else:
				return nil
		else:
			return nil

	# Returns an int giving a quad's relationship to its parent
	def relationToParent(self, quad):
		parent = quad.parent

		if (parent.ne == quad):
			return 1
		elif (parent.se == quad):
			return 2
		elif (parent.sw == quad):
			return 3
		elif (parent.nw == quad):
			return 4
		else:
			return -1
	"""
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
	"""
	
	def getCurrentRadiusInQuads(self):
		return 2**self.current_radius_exp

	def getLengthInNumberOfPossibleMinimalQuads(self):
		# NEED the + 1 because it's inclusive.
		return 2**((self.current_radius_exp - config.MIN_EXP))








		
