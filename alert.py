
import smtplib #the python class for smtp

def send_alert(GMAIL_PASSWORD, recipients, message):
    try:
        session = smtplib.SMTP('smtp.gmail.com', 587)   #creates new instance with gmail mobile smtp server
        session.ehlo()  #virtual handshake with server
        session.starttls()  #puts into TLS mode (aka encryption)
        session.ehlo()  #typically don't need to recall this but it only worked in plan9 when I did, some users suggest it
        session.login('leylinesapp@gmail.com', GMAIL_PASSWORD)
        session.sendmail('leylinesapp@gmail.com', recipients, message)
        session.quit()
        print "SENT ALERT"
    except:
        print "COULD NOT SEND ALERT"

#'recipients' can be either a list or a string, if it is a list then it will be sent as a group email
#   if you want individual emails you can for loop through the list and call the .sendmail function
#'message' is simply the body of the message
#   however, you can format it so the gmail smtp server translates it to html and distinguishes the subject from the body
