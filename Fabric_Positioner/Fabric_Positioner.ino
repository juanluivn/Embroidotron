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
const byte numLEDs = 2;
byte ledPin[numLEDs] = {7, 4};
byte ledStatus[numLEDs] = {0, 0};

const byte buffSize = 40;
char inputBuffer[buffSize];
const char startMarker = '<';
const char endMarker = '>';
byte bytesRecvd = 0;
boolean readInProgress = false;
boolean newDataFromPC = false;

float buffer_x[MAX_BUFFER_LENGTH];
float buffer_y[MAX_BUFFER_LENGTH];
int x_point_add = 0;
int y_point_add = 0;
int x_point_extract = 0;
int y_point_extract = 0;
/////////////////////////////////////////////////////////////////

int state = waiting_notMoved;
int i_needleDown = 1;
float next_x = 0;
float next_y = 0;
float x_ = 0;
float y_ = 0;
int needleFlag = 0;

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
      newDataFromPC = true;
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


  sendToPC();
}

void sendToPC() {
  Serial.print("<");
  Serial.print(x_point_add);
  Serial.print(">");
}
/////////////////////////////////////////////////////////////////

void setup() {
  Serial.begin(115200);

  // flash LEDs so we know we are alive
  for (byte n = 0; n < numLEDs; n++) {
     pinMode(ledPin[n], OUTPUT);
     digitalWrite(ledPin[n], HIGH);
  }
  delay(100); // delay() is OK in setup as it only happens once
  
  for (byte n = 0; n < numLEDs; n++) {
     digitalWrite(ledPin[n], LOW);
  }
  // tell the PC we are ready
  Serial.println("<Arduino is ready>");
  delay(1);
}

void loop() {
  if(i_needleDown < 21){
    switch (state) {
      case waiting_notMoved:
        // if the needle position is up switch to case 2
        if (1){//needleFlag == UP) {
          getDataFromPC();
//          sendToPC();

//          next_x = buffer_x[x_point_extract ++];
//          next_y = buffer_y[y_point_extract ++];
//          x_point_extract = x_point_extract % MAX_BUFFER_LENGTH;
//          y_point_extract = y_point_extract % MAX_BUFFER_LENGTH;

          state = needleUp_moving; // realizing that maybe this could be merged with the next state
        }
        break;
      case needleUp_moving:
        if (!fabPos.isMoving()) {
          fabPos.move_To(next_x, next_y);  // Moves the steppers to position X & Y via simple inverse kinematics
        }
        if (fabPos.isFinishedMoving()) {
          state = waiting_haveMoved;
        }
        break;
      case waiting_haveMoved:
        if (1){//needleFlag == DOWN) {
          state = waiting_notMoved;
        }
        break;
    }
  }
  else{
    // Embroidery is done
    digitalWrite(ledPin[0], HIGH);
    delay(1000);
    digitalWrite(ledPin[0], LOW);
    delay(200);
  }
}
