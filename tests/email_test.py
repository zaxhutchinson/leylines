#import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.mime.text import MIMEText

# Create a text/plain message
msg = MIMEText("THIS IS FROM LEYLINES. YOUR CHILD IS POSSIBLY IN DANGER. DO SOMETHING.")

smtp = 'smtp.rcn.com'
me = 'leylines@leylines.duckdns.org'
you  = 'Zachary.Hutchinson20@myhunter.cuny.edu'

# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = 'LEYLINES ALERT!!!!!!!'
msg['From'] = me
msg['To'] = you
# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP(smtp)
s.sendmail(me, [you], msg.as_string())
s.quit()
