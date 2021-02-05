// Include the AccelStepper library:
#include <AccelStepper.h>
#include "FabricPositioner.h"

// Define states
#define waiting_notMoved 1  // (1) Waiting for needle to come out of fabric -- have not moved
#define needleUp_moving 2   // (2) See needle is out of fabric -- moving
#define waiting_haveMoved 3 // (3) Wait for needle to re-enter fabric -- not moving, but have moved
#define UP 1
#define DOWN 0

#define MAX_BUFFER_LENGTH 10

////////////////////// GUI Interface ////////////////////////////
const int ledPin = 7;
const int buttonPin = 4;

const byte buffSize = 40;
char inputBuffer[buffSize];
const char startMarker = '<';
const char endMarker = '>';
byte bytesRecvd = 0;
boolean readInProgress = false;

float buffer_x[MAX_BUFFER_LENGTH];
float buffer_y[MAX_BUFFER_LENGTH];
int x_point_add = 0;
int y_point_add = 0;
int x_point_extract = 0;
int y_point_extract = 0;
/////////////////////////////////////////////////////////////////

int state = Wait;
int i_needleDown = 1;
float next_x = 0;
float next_y = 0;
float x_ = 0;
float y_ = 0;
volatile int needleFlag = 0;    // variable for reading needle status (button for now)
bool all_points = false;        // variable to indicate when we've stitched all points

float r1 = 15;
float r2 = 15;

FabricPositioner fabPos = FabricPositioner(r1, r2); // class to hold steppers and manage kinematics and motor control <-- TODO

////////////////////// GUI Interface ////////////////////////////
void getDataFromPC() {
  // Receive data from PC and save it into inputBuffer
  if(Serial.available() > 0) {
    char x = Serial.read();
    if (x == endMarker) {
      readInProgress = false;
      inputBuffer[bytesRecvd] = 0;
      parseData();
    }
    if(readInProgress) {
      inputBuffer[bytesRecvd ++] = x;
      if (bytesRecvd == buffSize) {
        bytesRecvd = buffSize - 1;
      }
    }
    if (x == startMarker) {
      bytesRecvd = 0; 
      readInProgress = true;
    }
  }
}

void parseData() {
  char* strtokIndx; // this is used by strtok() as an index
  strtokIndx = strtok(inputBuffer,","); // get the first part
  x_ = atof(strtokIndx);
  strtokIndx = strtok(NULL, ",");       // this continues where the previous call left off
  y_ = atof(strtokIndx);
  
  i_needleDown++;
  buffer_x[x_point_add ++] = x_;
  buffer_y[y_point_add ++] = y_;
  x_point_add = x_point_add % MAX_BUFFER_LENGTH;
  y_point_add = y_point_add % MAX_BUFFER_LENGTH;
  next_x = x_;
  next_y = y_;

  sendToPC(3);          // send to PC that the points were received
}

void sendToPC(int msg) {             
  Serial.print("<");
  if(msg == 1){
    Serial.print("FULL");
  }
  else if(msg == 2){
    Serial.print("NOT_FULL");
  }
  else if(msg == 3){
    Serial.print("RECEIVED");
  }
  else if(msg == 4){
    Serial.print("MOVED");
  }
  else if(msg == 5){
    Serial.print("DONE");
  }
  else if(msg == 6){
    Serial.print("Estop");
  }
  Serial.print(">");
}

void needleFlagButton() {
  needleFlag = UP;
}

/////////////////////////////////////////////////////////////////
/////////////////////// SETUP ///////////////////////////////////
void setup() {
  Serial.begin(2400);

  // Make the pushbutton's pin an input:
  pinMode(buttonPin, INPUT);
  // Attach an interrupt to button
  attachInterrupt(0, needleFlagButton, CHANGE); // 0 is for pin 2

  // flash LEDs so we know we are alive
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, HIGH);
  delay(100); // delay() is OK in setup as it only happens once
  digitalWrite(ledPin, LOW);
  
  // Tell PC we're ready
  Serial.println("<Arduino is ready>");
}

sendToPC("NOT_FULL")
getDataFromPC()
sendToPC("RECEIVED")
sendToPC("NOT_FULL")
getDataFromPC()
...
getDataFromPC()
sendToPC("RECEIVED")
sendToPC("FULL")
sendToPC("MOVED")


// MOVE WITH COMMUNICATION INDEPENDENTLY, USE INTERRUPTS FROM INCOMING needleFlag SIGNAL  <--

// NEED TO ADD WAY OF PARSING DATA NOT ONLY WHEN WE RECEIVE A POINT FROM PC               <--

/////////////////////// LOOP ///////////////////////////////////
void loop() {
// all_points --> if buffer is empty, set to True                                         <--
  if(){                                                                                   <--
    all_points = true;
    sendToPC(5);              // send to PC "DONE" to indicate design has finished
  }
  if(!all_points){
    switch (state) {
      case Wait:
        if(all_points){
          state = Done;       // move to Done
        }
        if(needleFlag == UP){
          state = Stitch;     // move to Stitch
        }
        break;
      case Stitch:
        if(needleFlag == DOWN){
          state = Estop;      // move to Estop
        }
        if(fabPos.isFinishedMoving()){
          state = Wait;       // move to Wait
          needleFlag = DOWN;  // set needleFlag to DOWN
        }
        break;
      case Done:
        sendToPC(5);          // send to PC that we're done
        break;
      case Estop:
        sendToPC(6);          // send to PC that the system had to do an emergency stop
        break;
    }
  }
  else{
    digitalWrite(ledPin, HIGH);
    delay(1000);
    digitalWrite(ledPin, LOW);
    delay(200);
  }
}
