
#include <AccelStepper.h>
#include "Arduino.h"
#include "FabricPositioner.h"

// Define stepper motor connections and motor interface type. Motor interface type must be set to 1 when using a driver:
#define xStepPin 2
#define xDirPin 5
#define yStepPin 3
#define yDirPin 6
#define MotorEnable 8
#define motorInterfaceType 1

#define notMoved 0
#define inMove 1

FabricPositioner::FabricPositioner(float r1, float r2){
  R1 = r1;
  R2 = r2;
  stepper_x = AccelStepper(motorInterfaceType, xStepPin, xDirPin);
  stepper_y = AccelStepper(motorInterfaceType, yStepPin, yDirPin);

  totalMoves = 0; // increases for every call of moveTo

  max_Speed = 2500;//1000;
  max_Accel = 500; // try 1000   // 30;
  setupSteppers();

  Dir1 = 1;
  Dir2 = -1;
  
  motionState = notMoved; // SOME BUGS COULD ARRISE FROM THIS VARIABLE
}

// Indicate if either x or y motors are moving
boolean FabricPositioner::isMoving(){
  // returns if either motor is running
  return stepper_x.isRunning() || stepper_y.isRunning();
}

// Marks the end of the move, this is run during each loop during motion
// If it's not moving and the state is inMove then we return true and change motion state to notMove
boolean FabricPositioner::isFinishedMoving(){
  if(!isMoving() && motionState == inMove){
    motionState = notMoved;
    return true;
  }
}

// Takes xy point and translates it to theta1 theta2, sends motors there
void FabricPositioner::move_To(float x, float y){
  motionState = inMove;
  totalMoves += 1;
  float Q1 = Dir1*x/R1*(100/PI);
  float Q2 = Dir1*y/R2*(100/PI);
  
  //assuming that we've zeroed the steppers so that
  // [x,y] = 0,0 corresponds to T1,T2 = [0,0]
  stepper_x.moveTo(Q1);
  stepper_y.moveTo(Q2);
  while(stepper_x.distanceToGo() != 0 || stepper_y.distanceToGo() != 0){
    stepper_x.run();
    stepper_y.run();
  }
}

// Stop movement of x and y motors (most likely used if motors are moving and needle goes back down)
void FabricPositioner::STOP(){
  stepper_x.stop();
  stepper_y.stop();
}

// Return total number of moves made
int FabricPositioner::getTotalMoves(){
  return totalMoves;
}

// Set up speed and acceleration for x and y motors
void FabricPositioner::setupSteppers(){
  // Set enable pin
  stepper_x.setEnablePin(MotorEnable);
  // Set minimum pulse width allowed by the stepper driver. The minimum practical pulse width is approximately 20 microseconds
//  stepper_x.enableOutputs();

  // Setup X motor
  stepper_x.setMaxSpeed(max_Speed);
  stepper_x.setAcceleration(max_Accel);

  // Setup Y motor
  stepper_y.setMaxSpeed(max_Speed);
  stepper_y.setAcceleration(max_Accel);

  // Reset X & Y Motors to zero position
  float Q1 = Dir1*20/R1*(100/PI);
  float Q2 = Dir1*10/R2*(100/PI);
  stepper_x.setCurrentPosition(Q1);
  stepper_y.setCurrentPosition(Q2);
}

void FabricPositioner::currentMotorPositions(){
  Serial.println("Current positions (x,y) are");
  Serial.println(stepper_x.currentPosition());
  Serial.println(stepper_y.currentPosition());
}







  
