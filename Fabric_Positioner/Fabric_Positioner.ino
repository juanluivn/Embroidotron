// Include the AccelStepper library:
#include <AccelStepper.h>
#include "FabricPositioner.h"

// Define states
#define Wait 1
#define Stitch 2
#define Done 3
#define Estop 4
#define UP 1
#define DOWN 0

#define MAX_BUFFER_LENGTH 10

////////////////////// GUI Interface ////////////////////////////
const int ledPin = 7;
const int buttonPin = 2;

const byte buffSize = 40;
char inputBuffer[buffSize];     // can use a queue for this buffer (FIFO)
const char startMarker = '<';
const char endMarker = '>';
byte bytesRecvd = 0;
boolean readInProgress = false;
boolean noMorePoints = false;

float buffer_points[MAX_BUFFER_LENGTH];
int point_add = 0;
int point_extract = 0;
/////////////////////////////////////////////////////////////////

int state = Wait;
int i_needleDown = 0;
float x_ = 0;
float y_ = 0;
float next_x = 0;
float next_y = 0;
volatile int needleFlag = 0;    // variable for reading needle status (button for now)
bool all_points = false;        // variable to indicate when we've stitched all points
bool E_Stop = false;
bool start = true;

float r1 = 15;
float r2 = 15;

FabricPositioner fabPos = FabricPositioner(r1, r2);

////////////////////// GUI Interface ////////////////////////////
void getDataFromPC() {
  // Receive data from PC and save it into inputBuffer
  if(Serial.available() > 0) {
    char x = Serial.read();
    if(x == endMarker) {
      readInProgress = false;
      inputBuffer[bytesRecvd] = 0;
      parseData();
    }
    if(readInProgress) {
      inputBuffer[bytesRecvd ++] = x;
      if(bytesRecvd == buffSize) {
        bytesRecvd = buffSize - 1;
      }
    }
    if(x == startMarker) {
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

  // Add received x and y points to the buffer
  buffer_points[point_add ++] = x_;
  buffer_points[point_add ++] = y_;

  if(x_ == -1){   // PC sends a -1 when we've covered all the points
    noMorePoints = true;
    point_add = point_add - 2;    // return point_add back two spaces so that it'll indicate full buffer
  }

  point_add = point_add % MAX_BUFFER_LENGTH;
} 

void sendToPC(int msg) {             // can use a map in this case (need to look into using library)
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

/////////////////////// LOOP ///////////////////////////////////
void loop() {
  if(!E_Stop){
    if(start){
      // Receive one point initially
      getDataFromPC();
      sendToPC(3);              // send to PC "RECEIVED" to indicate we've received the point (x_,y_)
      start = false;
    }
    if(noMorePoints && (point_add == point_extract)){       // No more points to move, i.e. design is done
      all_points = true;
      sendToPC(5);              // send to PC "DONE" to indicate design has finished
    }
    else if((point_add != point_extract) && !noMorePoints){ // Haven't received all, points and design not done
      sendToPC(2);              // send to PC "NOT_FULL" to indicate we can receive a point
      delay(10);
      getDataFromPC();
      sendToPC(3);              // send to PC "RECEIVED" to indicate we've received the point (x_,y_)
    }
    else if(point_add == point_extract){                    // Buffer is full and can't receive more points
      sendToPC(1);              // send to PC "FULL" to indicate buffer is full and hold off on sending
    }
    if(!all_points){
      switch (state) {
        case Wait:
          if(all_points){
            state = Done;       // move to Done
          }
          if(needleFlag == UP){
            state = Stitch;     // move to Stitch
            
            // Update next_x and next_y points to move the motors in Stitch state
            next_x = buffer_points[point_extract ++];
            next_y = buffer_points[point_extract ++];
            point_extract = point_extract % MAX_BUFFER_LENGTH;
          }
          break;
        case Stitch:
          if(needleFlag == DOWN){
            state = Estop;      // move to Estop
          }
          if (!fabPos.isMoving()) {
            fabPos.move_To(next_x, next_y);
          }
          if(fabPos.isFinishedMoving()){
            state = Wait;       // move to Wait
            needleFlag = DOWN;  // set needleFlag to DOWN
            i_needleDown++;
            sendToPC(4);        // send to PC "MOVED" to indicate motors moved successfully to next point
          }
          break;
        case Done:
          sendToPC(5);          // send to PC that we're done; we would never get here
          break;
        case Estop:
          sendToPC(6);          // send to PC that the system had to do an emergency stop
          E_Stop = true;
          break;
      }
    }
    else{
      while(true){
        digitalWrite(ledPin, HIGH);
        delay(1000);
        digitalWrite(ledPin, LOW);
        delay(200);
      }
    }
  }
}
