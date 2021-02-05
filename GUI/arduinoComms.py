import serial
import time
import sys
import glob
import pandas as pd
from tkinter import *
from tkinter.ttk import Progressbar

# global variables for module
startMarker = 60
endMarker = 62
designSize = 0

# ============================ Serial functions ============================
def listSerialPorts():
	# http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
	
    """Lists serial ports

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
    """
    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]

    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')

    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def setupSerial(serPort):
	global  ser
	
	# NOTE the user must ensure that the serial port and baudrate are correct
	#~ serPort = "/dev/ttyS81"
	baudRate = 2400#115200#9600
	ser = serial.Serial(serPort, baudRate)
	print("Serial port " + serPort + " opened  Baudrate " + str(baudRate))

	waitForArduino("Arduino is ready")

def closeSerial():
	global ser
	if 'ser' in globals():
		ser.close()
		print("Serial Port Closed\n\n")
	else:
		print("Serial Port Not Opened")

# ============================ Arduino functions ============================
def sendToArduino(sendStr):
	global startMarker, endMarker, ser
	
	ser.write(str.encode(chr(startMarker)))
	ser.write(str.encode(sendStr))
	ser.write(str.encode(chr(endMarker)))

def recvFromArduino(timeOut): # timeout in seconds eg 1.5
	global startMarker, endMarker, ser
  
	dataBuf = ""
	x = "z" # any value that is not an end- or startMarker
	startTime = time.time()
  
	# wait for the start marker
	while  ord(x) != startMarker: 
		if time.time() - startTime >= timeOut:
			return('<<')
		if ser.inWaiting() > 0: # because ser.read() blocks
			x = ser.read()
  

	# save data until the end marker is found
	while ord(x) != endMarker:
		if time.time() - startTime >= timeOut:
			return('>>')
		if ord(x) != startMarker:
			dataBuf = dataBuf + str(x, 'utf-8')
		if ser.inWaiting() > 0: # because ser.read() blocks
			x = ser.read()
		else:
			x = chr(startMarker) # crude way to prevent repeat characters
								 #   when no data is received
	return(dataBuf)

def waitForArduino(flag):
	# Wait for Arduino to send flag - allows time for Arduino to respond
	# Also ensures that any bytes left over from a previous message are discarded
	print("Waiting for Arduino")
    
	msg = ""
	while msg.find(flag) == -1:
		msg = recvFromArduino(10)	# 10 second timeout
		print(msg)
		print()

# ============================ Embroidotron functions ============================
def loadDesign():
	designFile = 'Circle.csv'
	global df
	df = pd.read_csv(designFile)
	designSize = len(df)
	print()
	print("Proceeding with design:", designFile)
	return designSize

def valToArduinoPoints(count):
	if(count < len(df)):
		x = df.iloc[count,0]
		y = df.iloc[count,1]
		sendStr = "%f,%f" %(x, y)
		print("Sending to Arduino: %s" %( sendStr))
		sendToArduino(sendStr)
	else:
		print("\nDesign is complete!")

