from tkinter import *
from tkinter.ttk import Progressbar
from arduinoComms import *
import atexit


# global variables for this module
ledAstatus = 0
ledBstatus = 0
count = 0
MAX_BUFFER_LENGTH = 10

tkArd = Tk()
tkArd.minsize(width=320, height=170)
tkArd.config(bg = 'yellow')
tkArd.title("Embroidotron 3000")

# Next line must come after  tkArd = Tk() so that a StringVar() can be created in checkForData
import arduinoCheckForData as cD	# So we can refer its variables

# ============================ Exit ============================
def exit_handler():
    print("\nMy application is ending!")
    cD.stopListening()
    closeSerial()

atexit.register(exit_handler)

# ============================ Setup Comm, GUI ============================
def setupView():
	global masterframe
	masterframe = Frame(bg = "yellow")
	masterframe.pack()
	selectPort()

def selectPort():
	global masterframe, radioVar
	for child in masterframe.winfo_children():
		child.destroy()
	
	radioVar = StringVar()
	lst = listSerialPorts()
	l1 = Label(masterframe, width = 5, height = 2, bg = "yellow")
	l1.pack()

	if len(lst) > 0:
		for n in lst:
			r1 = Radiobutton(masterframe, text=n, variable=radioVar, value=n, bg = "yellow")
			r1.config(command = radioPress)
			r1.pack(anchor = W)
	else:
		l2 = Label(masterframe, text = "No Serial Port Found")
		l2.pack()

def radioPress():
	setupSerial(radioVar.get())
	cD.listenForData()
	mainScreen()

def mainScreen():
	global masterframe
	for child in masterframe.winfo_children():
		child.destroy()

	labelA = Label(masterframe, width = 5, height = 2, bg = "yellow")
	labelB = Label(masterframe, width = 5, bg = "yellow")
	labelC = Label(masterframe, width = 5, bg = "yellow")
	
	progressbar = Progressbar(masterframe, orient = HORIZONTAL, length = 100, mode='determinate')
	
	ledAbutton = Button(masterframe, text="Start Embroidering", bg="black")
	ledAbutton.config(command = lambda: btnA(ledAbutton, progressbar, masterframe))
	
	ledBbutton = Button(masterframe, text="STOP", fg="red")
#	ledBbutton.config(command = lambda:  btnB(ledBbutton))
	
	labelA.grid(row = 0)
	ledAbutton.grid(row = 1)
	labelB.grid(row = 1, column = 2)
	ledBbutton.grid(row = 1, column = 3)
	labelC.grid(row = 2)
	progressbar.grid(row = 3, columnspan = 4)
	
def btnA(btn, progressbar, masterframe):
	global ledAstatus, ledBstatus, count
	
	if ledAstatus == 0:
		ledAstatus = 1
	else:
		ledAstatus = 0
	
	start_1 = time.time()
	
	safety = 0
	points_sent = 0
	motor_moves = 0
	while(True):
		if(safety > 1000):
			print("Breaking for safety")
		safety += 1

		textvariable = cD.displayVal
		if(textvariable == "NOT_FULL"):
			# Buffer is not full, can receive another point
			# If haven't sent all points, send point to Arduino
			if(count < numPoints):
				start = time.time()
				valToArduinoPoints(count)
				time.sleep(0.2)
				end2 = time.time()

				# Confirmation that the Arduino received the last point sent
				waitForArduino("RECEIVED")
				points_sent += 1
				print("\tNumber of points sent so far:", points_sent)
				# Increase index to next point
				count += 1
			# If we've sent all the points, don't do anything
			else:
				print("\tAll points have been sent")

			if(count == numPoints):
				# Wait to receive "DONE" message from Arduino
#				waitForArduino("DONE")
				print("\t\tTime for entire design: ",time.time() - start_1)
				print("The End")
				break
			else:
				print("\t\tTime taken: ",end2 - start,"\n")
		elif(textvariable == "FULL"):
			# Buffer is full, hold off on sending point
			print("\tBuffer is full, waiting until motors move to free up space")
			# Won't be able to send until buffer opens up one space
			# Therefore, wait for motors to move
			# Motors moved, buffer ready to receive another point
			waitForArduino("MOVED")
			motor_moves += 1
			print("\tMotors moved " + motor_moves + "time(s)")


# ============================ Run ============================
def runProgram():
	global numPoints
	numPoints = loadDesign()
	print("This design consists of", numPoints, "points")
	tkArd.mainloop()

# ============================ Main ============================
setupView()
runProgram()
