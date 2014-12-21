import socket
import sys

# Secret stop password
stop_msg = '666\nIAmCompletelySurroundedByNoBeer'

ADDRESS = sys.argv[1]
PORT = int(sys.argv[2])

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ADDRESS,PORT))
s.sendall (stop_msg)
data = s.recv(1024)
print(data)
s.close()
