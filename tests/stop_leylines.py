#Test client side communication

import socket

stop_msg = '666\nIAmCompletelySurroundedByNoBeer'

ADDRESS = 'leylines.duckdns.org:65006'
HOST = 'leylines.duckdns.org' 
PORT = 65006       

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST,PORT))

s.sendall (stop_msg)
while(True):
	None
#data1 = s.recv(1024)
#print(data1)
#s.sendall ('This is a test of the emergency system. If this were an actual emergency, you would quite possibly be dead.')

#data2 = s.recv(1024)
#s.close()
#print 'Received', repr(data1), '\n', repr(data2)
