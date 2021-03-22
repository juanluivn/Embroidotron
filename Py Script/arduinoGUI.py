# https://forum.arduino.cc/index.php?topic=598209.
# https://forum.arduino.cc/index.php?topic=45000.0
import serial
import time
import sys
from progress.bar import IncrementalBar
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt


startMarker = '<'
endMarker = '>'
dataStarted = False
dataBuf = ""
messageComplete = False
pointsSent = 0

#========================
def setupSerial(baudRate, serialPortName):
    global serialPort
    try:
        serialPort = serial.Serial(port = serialPortName, baudrate = baudRate, timeout = 0, rtscts = True)
        print("\nSerial port " + serialPortName + " opened with Baudrate " + str(baudRate))
        waitForArduino("Arduino is ready")
    except serial.serialutil.SerialException:
        print("\nThere's a problem setting up communication.")
        print("Make sure the Arduino is connected, the specified baud rate matches what is in the Arduino file,")
        print("and the serial port name matches what's outlined in the bottom right corner of the Ardunio console\n")
        raise serial.serialutil.SerialException
#        sys.exit()


#========================
def waitForArduino(flag):
    msg = ""
    while msg.find(flag) == -1:
        msg = recvFromArduino()


#========================
def sendToArduino(stringToSend):
    global startMarker, endMarker, serialPort, pointsSent
    
    if("," in stringToSend or "S" in stringToSend):
        if("," in stringToSend):
            pointsSent += 2
    stringWithMarkers = (startMarker)
    stringWithMarkers += stringToSend
    stringWithMarkers += (endMarker)
    serialPort.write(stringWithMarkers.encode('utf-8'))
    
    
#========================
def recvFromArduino():
    global startMarker, endMarker, serialPort, dataStarted, dataBuf, messageComplete

    if serialPort.inWaiting() > 0 and messageComplete == False:
        x = serialPort.read().decode("utf-8")
        if dataStarted == True:
            if x != endMarker:
                dataBuf = dataBuf + x
            else:
                dataStarted = False
                messageComplete = True
        elif x == startMarker:
            dataBuf = ''
            dataStarted = True
    if (messageComplete == True):
        messageComplete = False
        return dataBuf
    else:
        return "XXX"

    
#========================
def extractAndPrep(DesignFile):
    # Lists holding x and y values
    xs = []
    ys = []
    points = []

    if(DesignFile[-5:] == 'gcode'):			# Input design file is in GCODE format
        points_gcode = pd.read_csv(DesignFile, header=None, skiprows=3)
        for index, row in points_gcode.iterrows():
            word = row[0]
            if(word.find('X') > 0):
                x_ind = word.find('X')
                y_ind = word.find('Y')
                z_ind = word.find('Z')
                x = word[x_ind + 1:y_ind-1]
                y = word[y_ind + 1:z_ind-1]
                xs.append(float(x))
                ys.append(float(y))
                points.append([float(x), float(y)])
    elif(DesignFile[-3:] == 'csv'):			# Input design file is in CSV format
        points = pd.read_csv(DesignFile, header=None)
        points = points.values.tolist()
        for i in points:
            xs.append(i[0])
            ys.append(i[1])
    else:
        print("\nThere's a problem extracting the desing.")
        print("Make sure file you are choosing is in either csv or GCODE format\n")
        raise FileNotFoundError("Design file must be in CSV or GCODE format")

    ####### Dynamic plot showing progress
    xoffset = xs[0]
    yoffset = ys[0]
    for i in range(0,len(xs)):
        xs[i] -= xoffset
        xs[i] = round(xs[i], 1)
        ys[i] -= yoffset
        ys[i] = round(ys[i], 1)
        points[i] = [xs[i], ys[i]]
    points.append([-1,-1])
    xs.append(-1000)
    ys.append(-1000)

    if(len(xs) != len(ys)):
        print("\nThe number of x and y points don't match. Double check the design file.\n")
        raise Exception

    return xs, ys, points


#========================
def plotting(prep, movedReceived):
    if(prep):
        global x, y, fig, ax
        mpl.use('TkAgg')
        plt.ion()
        fig = plt.figure()
        ax = plt.subplot(1,1,1)
        x = []
        y = []
        ax.plot(x, y, 'x')
        fig.show()
        x.append(xs[0])
        y.append(ys[0])
        ax.lines[0].set_data(x, y)
        fig.canvas.flush_events()
    else:
        x.append(points[movedReceived][0])
        y.append(points[movedReceived][1])
        ax.lines[0].set_data(x, y)
        ax.relim()
        ax.autoscale_view()
        fig.canvas.flush_events()
        

#========================
# Define file to be used
#designFile = 'DesignFiles/GCode/PEmbroider_shape_hatching_1.gcode'
designFile = 'DesignFiles/Design1.csv'

# Extract and prepare the data from the specified design file
global xs, ys, points
xs, ys, points = extractAndPrep(designFile)

# Setup communication
setupSerial(115200, "/dev/tty.usbmodem14201")

# Turn on/off plotting feature
plottingOn = True
if(plottingOn):
    plotting(True, 0)

prevTime = time.time()
startTime = prevTime
numPoints = len(points)
print("\nDesign consists of %s points" % (numPoints - 1))
print("Starting the program\n")
sendToArduino("Starting")

# Progress bar showing number of stitches so far
bar = IncrementalBar('Progress ', max = numPoints - 1)

repliesReceived = 0
movedReceived = 0
FULL = False
noMorePoints = False

while True:
    arduinoReply = recvFromArduino()

    if (arduinoReply == "DONE"):
        print ("\n\nTime taken to complete design: %.6s seconds" % (time.time() - startTime))
        print("Sent to Arduino a total %s points" % (pointsSent))
        print("Received confirmation of %s points" % (repliesReceived))
        print("Motors have moved %s times\n" % (movedReceived))
        break

    #### See what flag has been received by the arduino
    if ("FULL_BUFFER" in arduinoReply and points):
        FULL = True
        waitForArduino("MOVED")
        movedReceived += 1
        sendToArduino("Sooooooo")
        if(plottingOn):
            plotting(False, movedReceived)
        bar.next()
    elif ("MOVED" in arduinoReply):
        movedReceived += 1
        if(plottingOn):
            plotting(False, movedReceived)
        bar.next()
    elif ("NOT_FULL" in arduinoReply) and points:
        FULL = False

    ##### Send to the Arduino
    if (time.time() - prevTime > 0.01) and xs and not (arduinoReply == "XXX") and not FULL:
        sendToArduino(str(xs[0]) + "," + str(ys[0]))
        prevTime = time.time()
        repliesReceived += 2
        if(xs):
            xs.pop(0)
            ys.pop(0)
        if not points:
            noMorePoints = True;

bar.finish()
