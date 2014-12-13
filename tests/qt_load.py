#!/usr/bin/python
import quadtree
import math
M_PI = 3.14159265358979323846264338327


def test():

	z_uid = "123456789abcde"

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
