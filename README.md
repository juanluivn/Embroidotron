# Embroidotron
A sewing-machine extension to provide embroidering capabilities
---
The goal of Embroidotron is to provide the ability to convert a sewing-machine to a CNC embroidery machine without permanent modification, at a moderate cost.
This repository serves as a source for the software, CAD documents and sample design files required to perform the modification.
---
GUI directory: contains a Python script, with two support Python files, and an Arduino program to perform communication between the Arduino and the computer.
  arduinoGUI.py
  arduinoComms.py
  arduinoCheckForData.py
  ArduinoGUICode/ArduinoGUICode.ino

Fabric_Positioner: contains an Arduino program with a defined class FabricPositioner.
  Fabric_Positioner.ino
  FabricPositioner.cpp
  FabricPositioner.h

Design_files: sample design files which users can use to test out embroidery.
  Circle.csv


