#!/usr/bin/python
import quadtree
import math
import time
import datetime
M_PI = 3.14159265358979323846264338327


def test():
	z_home = quadtree.GPSCoord(40.765130, -73.992942)
	z_time_01 = 
	z_data = quadtree.Data("It's me!")
	z_uid = "123456789abcde"
	z_fname = "Zachary"
	z_lname = "Hutchinson"
	z_time_block = 15

	# CREATE NEW PROFILE
	zax_profile = quadtree.Profile(z_uid, z_fname, z_lname, z_home, z_time_block, z_data)

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
