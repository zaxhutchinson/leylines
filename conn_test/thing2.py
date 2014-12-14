import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(('', 65006))

s.listen(100)

conn,addr = s.accept()

data = conn.recv(1024)
print(data)

address = addr

s.close()

s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s1.connect(address)

s1.sendall('HELLO WORLD BACK TO YOU')
