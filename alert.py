import smtplib #the python class for smtp
from email.mime.text import MIMEText

def send_alert(recipients, message):
	try:
		msg = MIMEText(message)
		me = 'leylines@leylines.duckdns.org'
		# me == the sender's email address
		# you == the recipient's email address
		msg['Subject'] = 'LEYLINES ALERT'
		msg['From'] = me
		msg['To'] = recipients
		# Send the message via our own SMTP server, but don't include the
		# envelope header.
		s = smtplib.SMTP(smtp)
		s.sendmail(me, [recipients], msg.as_string())
		s.quit()
		print("SENT ALERT")
	except:
		print("COULD NOT SEND ALERT")

