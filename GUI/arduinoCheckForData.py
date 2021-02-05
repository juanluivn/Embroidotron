from tkinter import *
import threading
import time

import arduinoComms as aC

# global variables for module
inputData = ""
threadRun = True
checkDelay = 0.1 # seconds # works when it's half of line 111

testVar = "testvar"
displayVal = ""
displayVal = "starting"

# ============================ Data ============================
def listenForData():
	t = threading.Thread(target=checkForData)
	t.daemon = True
	t.start()

def checkForData():
	global threadRun, checkDelay
	print("Starting to Listen")
	while threadRun == True:
		dataInput = aC.recvFromArduino(0.001)
		if dataInput == "<<" or dataInput == ">>":
			dataInput = "nothing"
		processData(dataInput)
		time.sleep(checkDelay)
	print("Finished Listening")

# function to illustrate the concept of dealing with the data
def processData(dataRecvd):
	global displayVal
	inputData = dataRecvd
	displayVal = dataRecvd

# ============================ Stop ============================
def stopListening():
	global threadRun, checkDelay
	threadRun = False
	time.sleep(checkDelay + 0.1) # allow Thread to detect end
