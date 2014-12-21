###################################################################
# Quadtree.py
#
# Not a generic implementation. Designed to be used by the Ley Lines
# system.
#
# The tree depends on the size of a quad being a power of 2.
#
# For some of the math helper functions that deal with GPS,
# distances are expected in meters.
#
# Throughout the code, each child quad is referred to by a direction
# which is also equated to an integer. This is done in a clockwise
# rotation, so for reference:
# 
# NE = 1
# SE = 2
# SW = 3
# NW = 4
#
# NOTE: When there is a call to save the tree to disk, the tree
# and its data objects are flattened into a dictionary. All data
# is extracted from the tree and stored according to a dataID,
# along with the midpoint of the quad in which it resided.
# Due to the excessive connectivity of the tree and the data objects
# it stores, the pickle module of python which handles serialization
# would often reach maximum recursion depth trying to delve the 
# tree's depths. To solve the issue, the tree must be flattened and
# the data connectivity severed in such a way it can be restored later.
# Some of this is explained in the misc.py Data class and also
# below in the flatten and rebuild tree functions.
#
###################################################################
import math
import pickle
import sys
import time
from collections import deque
import config
import alignment
import misc
##################################################################

# Quad Class:
# A quad tree is made up of quads. Each has four children.
# A reference to its parent is also stored.
class Quad:
	def __init__(self, parent, top_left, bottom_right):
		
		self.parent = parent
		
		# GPSCoord objects denoting the top_left and bottom_right
		# extremities of the quad.
		self.top_left = top_left
		self.bottom_right = bottom_right

		# The children
		self.ne = None
		self.se = None
		self.sw = None
		self.nw = None

		# If it is a leaf quad, data objects go here.
		self.data = []

# Quad Tree Class
class QuadTree:
	def __init__(self, coord, data = None):

		# This stores a reference to the last data object
		# added to the tree.
		self.prev_entry = None

		# The current radius' exponent (int) of the total tree.
		# See config.py for how this is initially calculated
		# and updated.
		self.current_radius_exp = config.RADIUS_EXP

		# The current radius of the tree.
		self.current_radius = self.getCurrentRadiusInQuads()
	
		# The tree's overall top_left and bottom_right GPSCoords.
		# Lat,Long
		top_left = self.getNewTopLeft( coord, self.current_radius )
		bottom_right = self.getNewBottomRight( coord, self.current_radius )

		# The root of the tree.
		self.root = Quad( None, top_left, bottom_right )

		##############################################################
		# Not implemented, or rather...not used.
		# Presently, they do get created, but they are not being
		# examined by Leylines.
		# 1 = Sunday, 7 = Saturday
		self.dodman_of_day = alignment.DateDodman()
		# Military time: format 0000 = midnight to midnight+time_block
		self.dodman_of_time = alignment.TimeDodman()
		##############################################################

		# Add the initial gps coordinate to the tree, catch result.
		result = self.addCoord( coord, self.root, self.current_radius, data )

		if( result != 0 ):
			print 'ERROR: creating quad tree. Exiting.'
			sys.exit(1)

	# Rebuilds the quad tree given a dictionary of data objects
	# The dictionary must have the following structure:
	#	dic[dataID] = (midpoint,data)
	def rebuildQuadTree(self, tree_as_dic):

		for i in range(1, len(tree_as_dic)):

			# If an id turns out not to be in the tree,
			# let me know. Vital debug output for testing
			# if the analyzer.py file loses data.
			if i not in tree_as_dic:
				print("DATAID does not exist: " + str(i))
				continue
			
			# Grab midpoint and data
			mid_point = tree_as_dic[i][0]
			data = tree_as_dic[i][1]

			# Reconnect references based on dataIDs
			if(data.prev_entry is not None):
				data.prev_entry = tree_as_dic[data.prev_entry][1]
			else:
				data.prev_entry = None
			if(data.next_entry is not None):
				data.next_entry = tree_as_dic[data.next_entry][1]
			else:
				data.next_entry = None

			# Toss back into the tree.
			self.addNewData(mid_point, data)
		
	# Flatten Tree (two functions)
	# Takes the quad tree and turns it into a dictionary with the
	# following structure:
	# dic[dataID] = (midpoint,data)
	def flattenTree(self):
		extracted_data = []
	
		# Pull out all data from tree and store in a list.
		sub_list = self.flattenQuadTree(self.root, self.getCurrentRadiusInQuads())

		# If the tree contained data (it better), extend our list.
		if( len(sub_list) > 0 ):
			extracted_data.extend(sub_list)

		data_dic = {}

		# For all the data in the extracted_data list,
		# create a dictionary and return it.
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

	# Should not be called directly. A recursive function that
	# turns the tree into a list.
	def flattenQuadTree(self, quad, radius):

		extracted_data = []

		# If we're at the bottom of the tree, add data & midpoint to list.
		if( radius <= config.QUAD_MIN ):
			mid_point = self.getMidPoint(quad.top_left, quad.bottom_right)
			for d in quad.data:
				extracted_data.append( (mid_point, d) )

		# Else, keep recursing
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

	# Add data to a leaf quad. Only used if we've reached the bottom
	# of the tree. Do not call directly.
	def addData(self, quad, data):

		quad.data.append(data)
		
		if( len(quad.data) >= config.MIN_VISITS_TO_CREATE_MEGALITH ):
			
			self.dodman_of_time.addQuad(data.time, quad)
			
			self.dodman_of_day.addQuad(data.time, quad)
		
		return

	# This is the main entry point for adding new data to the tree.
	def addNewData(self, coord, data):
		if( (self.addCoord( coord, self.root, self.getCurrentRadiusInQuads(), data)) == -2 ):
			return False
		else:
			return True

	# Does all the work in adding data to the tree.
	def addCoord(self, coord, quad, radius, data):

		# We're at the bottom of the tree, add new data
		if(radius <= config.QUAD_MIN):
			
			# Make all the connections to previous data
			if(data != None):
				data.location = quad
				data.prev_entry = self.prev_entry
			if(self.prev_entry != None):
				self.prev_entry.next_entry = data
			self.prev_entry = data

			# Add the new data.
			self.addData( quad, data )
			return 0
		
		# We're not at the bottom of the tree, so find out
		# which of the quad's four children this coordinate belongs.
		which_quad = self.getRelativeQuadrantForCoord( coord, quad.top_left, quad.bottom_right )
		mid_point = self.getMidPoint( quad.top_left, quad.bottom_right )

		# Based on which_quad, recursively call addCoord on the quad
		# our new coordinate belongs. If it's outside the bounds of the quad
		# we need to enlarge the tree.

		# MAJOR ERROR
		if( which_quad == -2 ):
			return -2

		# NOT IN QUAD, we must enlarge the tree.
		# NOTE: This check should be taken out of the work horse function.
		# Due to a rounding error (my guess), it is possible a coord falls 
		# outside a quad within
		# the tree and not the top quad. God knows what would happen then.
		elif( which_quad == -1 ):
			if( (self.enlargeQuadTree( coord )) == -2 ):
				return -2
			else:
				return self.addCoord( coord, self.root, self.getCurrentRadiusInQuads(), data )
		# NE
		elif( which_quad == 1 ):
			
			# If the quad does not exist, create a new one.
			if( quad.ne == None ):
				quad.ne = Quad( quad, 
							misc.GPSCoord(quad.top_left.latitude, mid_point.longitude),
							misc.GPSCoord(mid_point.latitude, quad.bottom_right.longitude) )
			
			# Recurse, baby, recurse...
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

	# Is this GPS Coordinate in the tree already?
	def isKnownCoord(self, coord):
		if(self.getLeafQuadForCoord(self.root, self.getCurrentRadiusInQuads(), coord) == None):
			return False
		else:
			return True

	# Is this GPS Coordinate within the last quad added to the tree.
	# NOTE: this can be done an easier way. Get location of prev_entry
	# and check against top_left and bottom_right.
	def isCoordInLastAddedQuad(self, coord):
		quad = self.getLeafQuadForCoord( self.root, self.getCurrentRadiusInQuads(), coord )

		if(quad == self.prev_entry):
			return True
		else:
			return False

	# For a given GPS Coordinate, return the quad in which it resides, if
	# said quad is in the tree, else return None.
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

	# Enlarge Quad Tree:
	# This gets called when a coordinate falls outside the present
	# tree. This continuously expands the tree by adding a new
	# root, thus increasing the area by 4 until the coordinate is
	# contained within the tree.
	#
	# It first determines in which direction from the present quadtree
	# the exterior coordinate lies (NE, SE, SW, NW) and expands the
	# geographically in that direction.
	def enlargeQuadTree( self, coord ):
		exterior_quadrant = self.getQuadrantForExteriorCoord( coord )

		new_root_top_left = None
		new_root_bottom_right = None

		new_root = None

		# IMPORTANT: expand the radius exponent so we know
		# how big the tree is.
		self.current_radius_exp += 1

		if(exterior_quadrant == 1):
			new_root_top_left = self.getGPSCoordByDirectionAndCourse( 
				self.root.top_left, self.getCurrentRadiusInQuads(), 0 )		
			new_root_bottom_right = self.getGPSCoordByDirectionAndCourse( 
				self.root.bottom_right, self.getCurrentRadiusInQuads(), 90 )
			new_root = Quad( None, new_root_top_left, new_root_bottom_right )
			new_root.sw = self.root
		elif(exterior_quadrant == 2):
			new_root_top_left = self.root.top_left
			new_lat = self.getGPSCoordByDirectionAndCourse( 
				self.root.bottom_right, self.getCurrentRadiusInQuads(), 90).longitude
			new_long = self.getGPSCoordByDirectionAndCourse( 
				self.root.bottom_right, self.getCurrentRadiusInQuads(), 180).latitude
			new_root_bottom_right = GPSCoord( new_lat, new_long )
			new_root = Quad(None, new_root_top_left, new_root_bottom_right )
			new_root.nw = self.root
		elif(exterior_quadrant == 3):
			new_root_top_left = self.getGPSCoordByDirectionAndCourse( 
				self.root.top_left, self.getCurrentRadiusInQuads(), 270)
			new_root_bottom_right = self.getGPSCoordByDirectionAndCourse( 
				self.root.bottom_right, self.getCurrentRadiusInQuads(), 90)
			new_root = Quad(None, new_root_top_left, new_root_bottom_right )
			new_root.ne = self.root
		elif(exterior_quadrant == 4):
			new_lat = self.getGPSCoordByDirectionAndCourse( 
				self.root.top_left, self.getCurrentRadiusInQuads(), 0).latitude
			new_long = self.getGPSCoordByDirectionAndCourse( 
				self.root.top_left, self.getCurrentRadiusInQuads(), 270).longitude
			new_root_top_left = GPSCoord( new_lat, new_long )
			new_root_bottom_right = self.root.bottom_right
			new_root = Quad(None, new_root_top_left, new_root_bottom_right )
			new_root.se = self.root
		elif(exterior_quadrant == -1):
			return -2 # MAJOR ERROR
		else:
			return -2 # MAJOR ERROR

		# Set new root
		self.root = new_root

	# DO NOT CALL DIRECTLY:
	# Used to expand the quad tree. Finds the direction of a coordinate
	# exterior to the quad tree.
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

	###############################################################
	# HELPER MATH FUNCTIONS

	# Swap radians to degrees
	def toDegrees( self, radians ):
		return radians * 180.0 / config.PI
	# Swap degrees to radians
	def toRadians( self, degrees ):
		return degrees * config.PI / 180.0

	# Calculate the distance between two GPS coordinates. Code
	# adapted and CORRECTED from a java example on stackoverflow (IIRC).
	# Correction based on another web source, pilots reference manual
	# from the 50's
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

	# Given a GPS Coordinate, a direction and distance, return the GPS
	# coordinate to which it refers. Adapted from several online references.
	def getGPSCoordByDirectionAndCourse( self, coord, distance, course ):
		course_in_radians = math.radians( course )
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

	# Used during quad tree creation to find the initial top_left and bottom_right
	# coordinates of the tree.
	def getNewTopLeft( self, coord, radius ):
		new_top = self.getGPSCoordByDirectionAndCourse( coord, radius, 0.0 )
		new_left = self.getGPSCoordByDirectionAndCourse( coord, radius, 270.0 )

		return misc.GPSCoord(new_top.latitude, new_left.longitude)
	def getNewBottomRight( self, coord, radius ):
		new_bottom = self.getGPSCoordByDirectionAndCourse( coord, radius, 180.0 )
		new_right = self.getGPSCoordByDirectionAndCourse( coord, radius, 90.0 )

		return misc.GPSCoord( new_bottom.latitude, new_right.longitude )

	# Get the mid point of the quad.
	def getMidPoint( self, quad ):
		return self.getMidPoint( quad.top_left, quad.bottom_right )

	# Get the midpoint of a given top_left and bottom_right
	def getMidPoint( self, top_left, bottom_right ):
		mid_lat = ( (top_left.latitude - bottom_right.latitude) / 2.0 ) + \
					bottom_right.latitude
		mid_long = ( (bottom_right.longitude - top_left.longitude) / 2.0) + \
					top_left.longitude

		return misc.GPSCoord( mid_lat, mid_long )

	# Get the midpoint of the last entry into the tree.
	def getPrevEntryLocationMidPoint(self):
		prev_quad = self.prev_entry.location

		return self.getMidPoint( prev_quad.top_left, prev_quad.bottom_right )

	# Given a quad, return the radius in meters.
	def getRadiusOfQuad( self, quad ):
		top_right = misc.GPSCoord( quad.top_left.latitude, quad.bottom_right.longitude )

		return (self.distanceBetweenTwoPoints( quad.top_left, top_right ) / 2.0)

	# Returns which child of a quad a particular coordinate belongs to.
	def getRelativeQuadrantForCoord( self, coord, quad ):
		return getRelativeQuadrantForCoord( coord, quad.top_left, quad.bottom_right )

	# Used by the above.
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

	# Finds the nearest quad in the tree to a specific coordinate
	# and returns the distance between it and the midpoint of the quad.
	def getDistanceToGoodQuad(self, coord):
		closest_good_quad = self.getClosestGoodQuad(coord)
		mid_point = self.getMidPoint(closest_good_quad.top_left,
										closest_good_quad.bottom_right)
		return self.distanceBetweenTwoPoints( mid_point, coord )

	# Finds the closest quad to a specific coordinate using Dijkstra's algo.
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

	# Is this coordinate in the tree?
	def isPointInTree(self, coord, container_quad):
		
		return self.isPointInTree(coord, self.root, self.getCurrentRadiusInQuads(), container_quad)

	
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








		
