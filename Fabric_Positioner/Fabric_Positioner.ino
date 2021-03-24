
const byte numChars = 10;
char receivedCharsX[numChars];
char receivedCharsY[numChars];
boolean readingX = true;
boolean newData = false;
boolean allPoints = false;

////////////////         ---Buffer---   ////////////////////////
#define ARRAY_SIZE(array) ((sizeof(array))/(sizeof(array[0])))
const int BUFFER_LENGTH = 10;
int buffer_points[BUFFER_LENGTH];
int points_a = 0;   // add
int points_e = 0;   // extract
int x = 0;
int y = 0;
bool FULL = false;
////////////////         ---Buffer---   ////////////////////////
////////////////           ---LED---    ////////////////////////
const int ledPin = 6;         // Y Dir
////////////////           ---LED---    ////////////////////////
////////////////  ---Needle Flag Interrupt---  /////////////////
const int buttonPin = 3;      // Y Step
volatile int needleFlag = 0;  // UP is 1, DOWN is 0
////////////////  ---Needle Flag Interrupt---  /////////////////
////////////////         ---Motors---   ////////////////////////
#include <AccelStepper.h>
#include <MultiStepper.h>
#define xStepPin 2
#define xDirPin 5
#define yStepPin 4            // Really Z Step
#define yDirPin 7             // Really Z Dir
#define MotorEnable 8
#define motorInterfaceType 1
AccelStepper stepper1;
AccelStepper stepper2;
MultiStepper steppers;
long positions[2] = {0, 0};
////////////////         ---Motors---   ////////////////////////


void needleFlagButton() {
    static unsigned long last_interrupt_time = 0;
    unsigned long interrupt_time = millis();
    if (interrupt_time - last_interrupt_time > 50)   // 200 works for button; may be different for Nano
    {
        needleFlag = 1;
    }
    last_interrupt_time = interrupt_time;
}

void setup() {
    Serial.begin(115200);

    //    LED Interrupt
    pinMode(ledPin, OUTPUT);
    digitalWrite(ledPin, LOW);

    //    Button Interrupt
    pinMode(buttonPin, INPUT);
    attachInterrupt(1, needleFlagButton, RISING); // 0 is for pin 2, 1 is for pin 3
    
    //    Motors
    stepper1 = AccelStepper(motorInterfaceType, xStepPin, xDirPin);
    stepper2 = AccelStepper(motorInterfaceType, yStepPin, yDirPin);
    stepper1.setMaxSpeed(100);//800);
    stepper2.setMaxSpeed(100);//800);
    steppers.addStepper(stepper1);
    steppers.addStepper(stepper2);
        
    Serial.println("<Arduino is ready>");
}

void loop() {
    if(needleFlag && !allPoints){
        positions[0] = long(buffer_points[points_e] * 1);
        points_e += 1;
        positions[1] = long(buffer_points[points_e] * 1);
        points_e += 1;
        digitalWrite(ledPin, HIGH);
        steppers.moveTo(positions);
        steppers.runSpeedToPosition(); // Blocks until all are in position
        digitalWrite(ledPin, LOW);

        points_e = points_e % BUFFER_LENGTH;
        Serial.print("<MOVED to ");
        Serial.print(positions[0]);
        Serial.print(", ");
        Serial.print(positions[1]);
        Serial.print(">");
        FULL = false;
        needleFlag = 0;

        if(buffer_points[points_e] == -1000){
            Serial.print("<DONE>");
            allPoints = true;
        }
    }
    recvWithStartEndMarkers();
    replyToPython();
}

void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;
  
    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();
        if (recvInProgress == true) {
            if (rc != endMarker && readingX){   // read X
                receivedCharsX[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else if(rc != endMarker){           // read y
                receivedCharsY[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                receivedCharsY[ndx] = '\0';
                recvInProgress = false;
                ndx = 0;
                newData = true;
                readingX = true;
            }
            if(rc == ','){
                receivedCharsX[ndx] = '\0';
                readingX = false;
                ndx = 0;
            }
        }
        else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
    x = atoi(receivedCharsX);
    y = atoi(receivedCharsY);
}

void replyToPython() {
    if (newData == true && !allPoints) {
        Serial.print("<*-*This just in from PC: __");
        Serial.print(receivedCharsX);
        if(receivedCharsX[0] != 'S'){
            buffer_points[points_a] = x;
            points_a += 1;
            buffer_points[points_a] = y;
            points_a += 1;
            points_a = points_a % BUFFER_LENGTH;
            if(points_a == points_e){
                FULL = true;
            }
            Serial.print(receivedCharsY);
            Serial.print("__; (x,y):");
            Serial.print(x);
            Serial.print(",");
            Serial.print(y);
        }
        else{
            Serial.print("__;");          
        }
        Serial.print(", ");
        Serial.print("points_a = ");
        Serial.print(points_a);
        Serial.print(", points_e = ");
        Serial.print(points_e);
        if(FULL){
            Serial.print(", FULL_BUFFER");
        }
        else{
            Serial.print(", NOT_FULL");
        }
        Serial.print(", len(buffer_points) = ");
        Serial.print(ARRAY_SIZE(buffer_points));
        Serial.print("\n\t");
        for(int i = 0; i < ARRAY_SIZE(buffer_points); i ++){
            if(i == points_a){
                Serial.print("[");
                Serial.print(buffer_points[i]);
                Serial.print("], ");
            }
            else if(i == points_e){
                Serial.print("(");
                Serial.print(buffer_points[i]);
                Serial.print("), ");
            }
            else{
                Serial.print(buffer_points[i]);
                Serial.print(", ");
            }
        }
        Serial.print("\t*-*>");
        newData = false;
    }
}
