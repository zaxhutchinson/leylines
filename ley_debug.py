############################################
# ley_debugger.py
#
# Print messages to console, if debugging is on.
#
###########################################
class Debugger:
	def __init__(self, is_active=False):
		self.is_active = is_active

	def makeActive(self):
		self.is_active = True

	def makeInactive(self):
		self.is_active = False

	def debugMsg(self, msg):
		if(self.is_active):
			print(msg)
