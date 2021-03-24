import serial
import time
import sys
from progress.bar import IncrementalBar
import pandas as pd
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches


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
def extractAndPrep(DesignFile, width, length):
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

    ####### List for dynamic plot showing progress
    xoffset = min(xs)
    yoffset = min(ys)
    xdiff = max(xs) - min(xs)
    ydiff = max(ys) - min(ys)
    for i in range(0,len(xs)):
        xs[i] -= xoffset
        xs[i] = round(xs[i], 1) + width/2 - xdiff/2
        ys[i] -= yoffset
        ys[i] = round(ys[i], 1) + length/2 - ydiff/2
        points[i] = [xs[i], ys[i]]

    points.append([-1,-1])
    xs.append(-1000)
    ys.append(-1000)

    if(len(xs) != len(ys)):
        print("\nThe number of x and y points don't match. Double check the design file.\n")
        raise Exception

    return xs, ys, points


#========================
def plotting(prep, movedReceived, width = 1, length = 1):
    if(prep):
        global x, y, fig, ax
        mpl.use('TkAgg')
        plt.ion()
        fig, ax = plt.subplots()
        ax.set_axisbelow(True)
        ax.minorticks_on()

        x = []
        y = []
        margin = 50
        ax.plot(x, y, 'x', markersize=1)
        fig.show()
        x.append(xs[0])
        y.append(ys[0])
        ax.lines[0].set_data(x, y)
        outer = patches.FancyBboxPatch((0,0), width, length, boxstyle = "round,rounding_size=20",fc = "none", ec='black', label='Hoop')
        outer2 = patches.FancyBboxPatch((-margin,-margin), width + 2*margin, length + 2*margin, boxstyle = "round,rounding_size=20",fc = "none", ec='black', label='Hoop')
        rect = patches.Rectangle((margin, margin), width - 2*margin, length - 2*margin, linestyle='--', fc = "none", ec='red', label='Work area')
        ax.add_patch(outer)
        ax.add_patch(outer2)
        ax.add_patch(rect)
        ax.plot(width/2, length/2, '+', markersize=50, color='g', alpha=0.3) # Add marker indicating center of work area
        plot_margin = 100
        ax.set_xlim([0 - plot_margin, width + plot_margin])
        ax.set_ylim([0 - plot_margin, length + plot_margin])
        ax.grid(which = 'major', linestyle = '-', linewidth = '0.5', color = 'blue', alpha = 0.2)
        ax.grid(which = 'minor', linestyle = ':', linewidth = '0.5', color = 'black', alpha = 0.1)
        plt.axis('equal')
        plt.legend(handles=[rect,outer])
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
designFile = 'DesignFiles/GCode/PEmbroider_shape_hatching_1.gcode'
#designFile = 'DesignFiles/Design4.csv'   # 0000 is y

# Define size of embroidery hoop in use in inches
#100 steps --> 0.75 inches: CF of 0.0075
#300 steps --> 2.375 inches:CF of 0.0079
maxX = 13  # width of hoop   --> 633 (5 in.); result: 4.99 in.
maxY = 5   # length of hoop  --> 380 (3 in.); result: 2.99 in.
margin = 1
conversionFactor = 0.0079   # 0.0079 inches/unit(aka step)
X = math.ceil(maxX/conversionFactor)
Y = math.ceil(maxY/conversionFactor)

# Extract and prepare the data from the specified design file
global xs, ys, points
xs, ys, points = extractAndPrep(designFile, X, Y)

# Check if design is within bounds of the hoop
print("\nChecking if design is within bounds of the hoop...")
if(max(xs) < (X - margin) and max(ys) < (Y - margin)):
    print("Design looks good! Proceeding with embroidery.\n")
    print("--------------------REMINDER--------------------")
    print("Remember to line up the needle at the (0,0) mark of the hoop, i.e. the bottom left position of the hoop.")
    print("Also, move the wheel manually for the first point to get the motors to move to the starting position.")
    print("------------------------------------------------")
else:
    print("Design seems too big for the hoop in use and defined. Please either scale the design or change to a larger hoop.\n")
    raise Exception

# Turn on/off plotting feature
plottingOn = True
visualizingMode = True
if(plottingOn):
    plotting(True, 0, X, Y)
    
# Either choose to only visualize a design and see results or, when ready, run through the program and embroider
repliesReceived = 0
movedReceived = 0
numPoints = len(points)
if(visualizingMode):
    while(True):
        if(movedReceived == numPoints):
            break
        plotting(False, movedReceived)
        movedReceived += 1
    time.sleep(5)
else:
    # Add an additional point to give the motors a chance to get to the first point before starting the design
    xs.insert(0, xs[0])
    ys.insert(0, ys[0])
    points.insert(0, points[0])

    # Setup communication
    setupSerial(115200, "/dev/tty.usbmodem14201")

    prevTime = time.time()
    startTime = prevTime
    print("\nDesign consists of %s points" % (numPoints - 2))   # 2 extra points are the extra initial point added and negative points indicating ending of design
    print("Starting the program\n")
    sendToArduino("Starting")

    # Progress bar showing number of stitches so far
    bar = IncrementalBar('Progress ', max = numPoints - 2)

    FULL = False
    noMorePoints = False
    readyToEmbroider = False

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
            if(readyToEmbroider):
                bar.next()
        elif ("MOVED" in arduinoReply):
            movedReceived += 1
            if(plottingOn):
                plotting(False, movedReceived)
            if(readyToEmbroider):
                bar.next()
        elif ("NOT_FULL" in arduinoReply) and points:
            FULL = False

        if(not readyToEmbroider and movedReceived > 0):
            print("\n\nMotors are in the starting position, you're all set to start embroidering!")
            readyToEmbroider = True

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
