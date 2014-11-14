import datetime
import time


#d = datetime.datetime.fromtimestamp(time.time())

f = open('times.txt', 'w')


for i in range(0,100):

	t = str(int(time.time()))
	
	f.write(t)
	f.write("\n")

	time.sleep(5)


f.close()
