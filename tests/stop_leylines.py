#Test client side communication

import socket

stop_msg = '666\nIAmCompletelySurroundedByNoBeer'
init_msg = 'I\n1234567890\n40.765411\n-73.993610\n1'

ADDRESS = 'leylines.duckdns.org:65006'
HOST = 'leylines.duckdns.org'
HOST_LOCAL = 'localhost'
PORT = 65006       
PORT_LOCAL = 65006

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.connect((HOST,PORT))
s.connect((HOST_LOCAL,PORT_LOCAL))
s.sendall (stop_msg)
#s.sendall(init_msg)
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
