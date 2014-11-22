#!/usr/bin/python
import quadtree
import math
import time
import datetime
import random
import config
import sys

from PIL import Image
from PIL import ImageDraw

def drawQuadTree(profile):

	length = profile.tree.getLengthInNumberOfPossibleMinimalQuads()
	
	im = Image.new("RGB", (length,length), "white")
	draw = ImageDraw.Draw(im)

	exp = (profile.tree.current_radius_exp - config.MIN_EXP)

	clockwiseDraw( profile.tree.root, exp, 0, 0, draw )

	del draw
	im.save(profile.uid + ".png")

def clockwiseDraw(quad, exp, x, y, draw):

	length = 2**exp

	if(exp == 0):
		if( quad != None ):
			for j in range ( y, (y + length)):
				for i in range (x, (x + length)):
					if( len(quad.data) > 0 ):
						draw.point( (i, j), "black" )
					"""elif( len(quad.data) == 2 ):
						draw.point( (i, j), "yellow" )
					elif( len(quad.data) == 3 ):
						draw.point( (i, j), "orange" )
					elif( len(quad.data) == 4 ):
						draw.point( (i, j), "red" )
					elif( len(quad.data) == 5 ):
						draw.point( (i, j), "pink")
					elif( len(quad.data) >= 6 ):
						draw.point( (i, j), "white")"""

		return

	else:
		if(quad != None):
			clockwiseDraw(quad.ne, exp-1, (x + (2**(exp-1))), y, draw)
			clockwiseDraw(quad.se, exp-1, (x + (2**(exp-1))), (y + (2**(exp-1))), draw)
			clockwiseDraw(quad.sw, exp-1, x, (y + (2**(exp-1))), draw)
			clockwiseDraw(quad.nw, exp-1, x, y, draw)


def test():

	sys.setrecursionlimit(100000)

	z_home = quadtree.GPSCoord(40.765130, -73.992942)
	z_times = []
	z_locs = []
	z_data = quadtree.Data("It's me!")
	z_uid = "123456789abcde"
	z_fname = "Zachary"
	z_lname = "Hutchinson"

	f = open('times.txt', 'r')
	for line in f:
		z_times.append(line.rstrip())
	
	"""
	for i in range(0,100):
		lat_noise = random.uniform(-0.01, 0.01)	
		long_noise = random.uniform(-0.01, 0.01)

		z_locs.append( quadtree.GPSCoord( (z_home.latitude + lat_noise), (z_home.longitude + long_noise) ) )

	f.close()
	"""

	f = open('zac_path.path', 'r')

	for line in f:
		gps = line.split(',')
		lat = gps[0].strip()
		lon = gps[1].strip()

		z_locs.append( quadtree.GPSCoord( float(lat), float(lon) ) )

	f.close()


	# CREATE NEW PROFILE
	zax_profile = quadtree.Profile(z_uid, z_fname, z_lname, z_home, z_data)
	
	t = time.time()

	# Create data objects and add to tree
	for i in range(0,len(z_locs)):

		#d = quadtree.Data( z_times[i] ) 
		d = quadtree.Data( t )
		check = zax_profile.addNewData( z_locs[i], d )

		if(check == False):
			print("FUCK UP")


	# SAVE IT
	zax_profile.save()

	# DESTROY THE ONE IN MEMORY
	zax_profile = None

	# LOAD IT UP
	zax_profile = quadtree.Profile.load(z_uid)

	# PRINT PROFILE FIRST NAME
	print(zax_profile.first_name)

	drawQuadTree(zax_profile)

	# PRINT ENTIRE TREE
	# zax_profile.tree.printTree(zax_profile.trees.root)


	


if __name__ == '__main__':
	test()
