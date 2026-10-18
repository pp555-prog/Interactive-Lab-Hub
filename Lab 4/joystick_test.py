from __future__ import print_function
import qwiic_joystick
import time
import sys

def runExample():

	print("\nSparkFun qwiic Joystick   Example 1\n")
	myJoystick = qwiic_joystick.QwiicJoystick()

	if myJoystick.connected == False:
		print("The Qwiic Joystick device isn't connected to the system. Please check your connection", \
			file=sys.stderr)
		return

	myJoystick.begin()

	print("Initialized. Firmware Version: %s" % myJoystick.version)

	while True:

		# our board is mounted rotated 90 degrees, so swap the axes:
		# X is left (0) to right (1023), Y is toward (0) to away (1023)
		# the raw button reads 0 when pressed, so invert it: 1 = pressed
		print("X: %d, Y: %d, Button: %d" % ( \
					myJoystick.vertical, \
					myJoystick.horizontal, \
					1 - myJoystick.button))

		time.sleep(.5)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example 1")
		sys.exit(0)