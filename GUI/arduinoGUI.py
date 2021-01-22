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

def exit_handler():
    print("\nMy application is ending!")
    cD.stopListening()
    closeSerial()

atexit.register(exit_handler)


# ---------------- Setup Comm and GUI ----------------
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
	
	l1= Label(masterframe, width = 5, height = 2, bg = "yellow")
	l1.pack()

	if len(lst) > 0:
		for n in lst:
			r1 = Radiobutton(masterframe, text=n, variable=radioVar, value=n, bg = "yellow")
			r1.config(command = radioPress)
			r1.pack(anchor=W)
	else:
		l2 = Label(masterframe, text = "No Serial Port Found")
		l2.pack()

def radioPress():
	global radioVar
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
	for i in range(count, numPoints + 1):

		textvariable = cD.displayVal
		print("\tNumber of points so far:", textvariable)
		# text variable is a string
		try:
			int(textvariable)
			# While loop here that iterates until textvariable is less than
			# MAX_BUFFER_LENGTH - 1. This should allow getting rid of time.sleep
#			print("Now it's an int")
		except:
#			print("Not an int yet")
			print("")

		start = time.time()
		valToArduinoPoints(count)

		time.sleep(0.2)
		end2 = time.time()
		if i == numPoints:
			print("\t\tTime for entire design: ",end2 - start_1)
			print("The End")
			break
		else:
			print("\t\tTime taken: ",end2 - start,"\n")
		count += 1

def btnB(btn):
	global ledAstatus, ledBstatus, count
	
	if ledBstatus == 0:
		ledBstatus = 1
		btn.config(fg="red", relief=SUNKEN)
	else:
		ledBstatus = 0
		btn.config(fg="black")
	for i in range(count,):
		print()
	valToArduinoLED(ledAstatus, ledBstatus)
	valToArduinoPoints(count)
	count += 1

def bar(progress, root, count):
    progress['value'] = count * 5
    root.update_idletasks()

# ---------------- Run program ----------------
def runProgram():
	global numPoints
	numPoints = loadDesign()
	print("This design consists of", numPoints, "points")
	tkArd.mainloop()

# ---------------- Main ----------------
setupView()
runProgram()
