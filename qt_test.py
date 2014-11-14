#!/usr/bin/python
import quadtree
import math
import time
import datetime
import random
M_PI = 3.14159265358979323846264338327


def test():
	z_home = quadtree.GPSCoord(40.765130, -73.992942)
	z_times = []
	z_locs = []
	z_data = quadtree.Data("It's me!")
	z_uid = "123456789abcde"
	z_fname = "Zachary"
	z_lname = "Hutchinson"
	z_time_block = 15

	f = open('times.txt', 'r')
	for line in f:
		z_times.append(line)

	for i in range(0,100):
		lat_noise = random.uniform(-0.001, 0.001)	
		long_noise = random.uniform(-0.001, 0.001)

		z_locs.append( quadtree.GPSCoord( (z_home.latitude + lat_noise), (z_home.longitutde + long_noise) ) )

	# CREATE NEW PROFILE
	zax_profile = quadtree.Profile(z_uid, z_fname, z_lname, z_home, z_time_block, z_data)
	
	# Create data objects and add to tree

	# SAVE IT
	zax_profile.save()

	# DESTROY THE ONE IN MEMORY
	zax_profile = None

	# LOAD IT UP
	zax_profile = quadtree.Profile.load(z_uid)

	# PRINT PROFILE FIRST NAME
	print(zax_profile.first_name)

	# PRINT ENTIRE TREE
	zax_profile.trees.printTree(zax_profile.trees.root)




if __name__ == '__main__':
	test()
