# server side communication attempt

import socket
import Queue 
stile = Queue.Queue()

HOST = ''        #Denotes all available interfaces (whatever that means)
PORT = 50007     #Some non-priviledged port 

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((HOST, PORT))

s.listen(2)

conn, addr = s.accept()

print 'Conncected by', addr

while (1):

   data = conn.recv(1024)
   stile.put(data)

   if not data :break
   conn.sendall(data)

while (stile.qsize() > 0):
    print stile.get()
conn.close()
