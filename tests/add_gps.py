#Test client side communication

import socket

stop_msg = '666\nIAmCompletelySurroundedByNoBeer'
init_msg = 'I\n1234567890\n40.765411\n-73.993610\n1'
pos_msg = 'G\n1234567890'

f = open('zac_path.path','r')
locations = []
time = 0
take_five = 300
for line in f:
	line = line.strip()
	gps = line.split(',')
	pos_msg += ('\n' + gps[0])
	pos_msg += ('\n' + gps[1])
	pos_msg += ('\n' + str(time))
	time += take_five
f.close()

ADDRESS = 'leylines.duckdns.org:65006'
HOST = 'leylines.duckdns.org'
HOST_LOCAL = 'localhost'
PORT = 65006       
PORT_LOCAL = 65006

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.connect((HOST,PORT))
s.connect((HOST_LOCAL,PORT_LOCAL))
#s.sendall(init_msg)
s.sendall(pos_msg)
#s.sendall (stop_msg)
data = s.recv(1024)
print(data)
s.close()
#while(True):
#	None
#data1 = s.recv(1024)
#print(data1)
#s.sendall ('This is a test of the emergency system. If this were an actual emergency, you would quite possibly be dead.')

#data2 = s.recv(1024)
#s.close()
#print 'Received', repr(data1), '\n', repr(data2)
