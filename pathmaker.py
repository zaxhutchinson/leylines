
thirty_two_meters = 0.0005

class GPS:
	def __init__(self, lat, lon):
		self.lat = lat
		self.lon = lon

def getY( slope, x, GPSCoord ):
	return (slope * (x - GPSCoord.lon)) + GPSCoord.lat

def getX( slope, y, GPSCoord ):
	return ((y - GPSCoord.lat) / slope) + GPSCoord.lon

def pathmaker( path_list, GPS1, GPS2 ):

	slope = (GPS1.lat - GPS2.lat) / (GPS1.lon - GPS2.lon)

	if( abs(GPS1.lon - GPS2.lon) > abs(GPS1.lat - GPS2.lat) ):
		if( GPS1.lon < GPS2.lon):

			lon = GPS1.lon
			while( lon < GPS2.lon ):

				lat = getY(slope, lon, GPS2)

				path_list.append(GPS(lat,lon))

				lon += thirty_two_meters

		else:
			lon = GPS2.lon

			while( lon < GPS1.lon ):
				lat = getY(slope, lon, GPS1)

				path_list.append(GPS(lat,lon))

				lon += thirty_two_meters

	else:
		if( GPS1.lat < GPS2.lat ):

			lat = GPS1.lat

			while( lat < GPS2.lat ):

				lon = getX(slope, lat, GPS2)

				path_list.append(GPS(lat, lon))

				lat += thirty_two_meters

		else:
			lat = GPS2.lat

			while( lat < GPS1.lat ):

				lon = getX(slope, lat, GPS1)

				path_list.append(GPS(lat,lon))

				lat += thirty_two_meters



path_list = []

a = GPS(40.765523, -73.993878) # house
b = GPS(40.756519, -73.972399) # lex & 50
c = GPS(40.767880, -73.964074) # hunter
d = GPS(40.769915, -73.968871) # 5th & 68
e = GPS(40.764316, -73.973002) # 5th & 59
f = GPS(40.766876, -73.979053) # 7th & CPS
g = GPS(40.761098, -73.983301) # 7th & 50
h = GPS(40.765540, -73.993825) # house
i = GPS(40.765873, -73.994651) # 11 & 50
j = GPS(40.792687, -73.975082) # WE & 92
k = GPS(40.789105, -73.966596) # CPW & 92
l = GPS(40.785289, -73.969341) # CPW & 86
m = GPS(40.779489, -73.955544) # Lex & 86
n = GPS(40.767843, -73.964075) # Lex & 68
o = GPS(40.769225, -73.967261) # Mad & 68
p = GPS(40.767331, -73.968656) # Mad & 65
q = GPS(40.767965, -73.970265) # 5th & 65
r = GPS(40.758563, -73.977217) # 5th & 50
s = GPS(40.765536, -73.993847) # house
t = GPS(40.764674, -73.991756) # 10 & 50
u = GPS(40.759619, -73.995468) # 10 & 42
v = GPS(40.756921, -73.988998) # movie
w = GPS(40.758417, -73.992636) # 9 & 42
x = GPS(40.763504, -73.988945) # 9 & 50
y = GPS(40.765584, -73.993923) # house


locs = [a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y]

for i in range(0,(len(locs)-1)):

	pathmaker(path_list, locs[i], locs[i+1])


f = open('zac_path.path', 'w')

for p in path_list:
	f.write(str(p.lat) + ',' + str(p.lon) + '\n')

f.close()
