# Test client side communication

import socket

HOST = 'leylines.duckdns.org'  # remote host 
PORT = 65006           # This port must match the server side number

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((HOST, PORT))

s.sendall ('Hello World')
data1 = s.recv(1024)
s.sendall ('This is a test of the emergency system. If this were an actual emergency, you would quite possibly be dead.')

data2 = s.recv(1024)

s.close()
print 'Received', repr(data1), '\n', repr(data2) 
