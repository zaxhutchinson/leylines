#!/usr/bin/python
import quadtree
import math
import time
import datetime
import random
import config

#from tkinter import *
#from tkinter import ttk

from PIL import Image
from PIL import ImageDraw
"""
#class Map(TopLevel):
class QTMap():
	def __init__(self):
	#def __init__(self, *args, **kwargs):
		#Tk.__init__(self, *args, **kwargs)
		
		self.main = ttk.Frame(self)

		self.scrollX = Scrollbar(self.main, orient=HORIZONTAL)
		self.scrollY = Scrollbar(self.main, orient=VERTICAL)

		self.quad_map = Canvas(self.main,
				scrollregion=(0,0,10000,10000),
				xscrollcommand=self.scrollX.set,
				yscrollcommand=self.scrollY.set)
		self.quad_map.config(bg="#000000", height=800, width=800)
		self.quad_map.grid(column=0,row=0,sticky=N+E+S+W)

		self.scrollX.config(command.self.quad_map.xview)
		self.scrollY.config(command.self.quad_map.yview)
		self.scrollX.grid(column=0,row=1,columnspan=2,sticky=N+E+W+S)
		self.scrollY.grid(column=1,row=0,rowspan=2,sticky=N+E+S+W)

		self.main.grid(column=0, row=0, sticky=N+E+S+W)
"""
def drawQuadTree(profile):

	length = profile.tree.getLengthInNumberOfPossibleMinimalQuads()
	
	im = Image.new("RGB", (length,length), "black")
	draw = ImageDraw.Draw(im)

	exp = (config.RADIUS_EXP - config.MIN_EXP) + 1

	clockwiseDraw( profile.tree.root, exp, 0, 0, draw )

	del draw
	im.save(profile.uid + ".png")

def clockwiseDraw(quad, exp, x, y, draw):
	
	length = 2**exp
	print(length)

	if(quad != None):
		
		clockwiseDraw(quad.ne, exp-1, (x + (2**(exp-1))), y, draw)
		clockwiseDraw(quad.se, exp-1, (x + (2**(exp-1))), (y + (2**(exp-1))), draw)
		clockwiseDraw(quad.sw, exp-1, x, (y + (2**(exp-1))), draw)
		clockwiseDraw(quad.nw, exp-1, x, y, draw)

	else:
		if( exp == 0):
			print(x, y)
			for j in range ( y, (y + length)):
				for i in range (x, (x + length)):
					draw.point( (i, j), "white" )



def test():
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

	for i in range(0,100):
		lat_noise = random.uniform(-0.01, 0.01)	
		long_noise = random.uniform(-0.01, 0.01)

		z_locs.append( quadtree.GPSCoord( (z_home.latitude + lat_noise), (z_home.longitude + long_noise) ) )

	# CREATE NEW PROFILE
	zax_profile = quadtree.Profile(z_uid, z_fname, z_lname, z_home, z_data)
	
	# Create data objects and add to tree
	for i in range(0,99):

		d = quadtree.Data( z_times[i] ) 

		zax_profile.addNewData( z_locs[i], d )

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
