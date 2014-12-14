import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(('leylines.duckdns.org',65006))

s.sendall('HELLO WORLD\n')

data1 = s.recv(1024)

print(data1)
