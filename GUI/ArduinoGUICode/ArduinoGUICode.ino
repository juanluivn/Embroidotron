
const byte numLEDs = 2;
byte ledPin[numLEDs] = {4, 7};
byte ledStatus[numLEDs] = {0, 0};
const byte buffSize = 40;
char inputBuffer[buffSize];
const char startMarker = '<';
const char endMarker = '>';
byte bytesRecvd = 0;
boolean readInProgress = false;
boolean newDataFromPC = false;
unsigned long curMillis;

void setup() {
  Serial.begin(2400); //   Serial.begin(115200);
  
  // flash LEDs so we know we are alive
  for (byte n = 0; n < numLEDs; n++) {
     pinMode(ledPin[n], OUTPUT);
     digitalWrite(ledPin[n], HIGH);
  }
  delay(500); // delay() is OK in setup as it only happens once
  
  for (byte n = 0; n < numLEDs; n++) {
     digitalWrite(ledPin[n], LOW);
  }
    
  // tell the PC we are ready
  Serial.println("<Arduino is ready>");
}

void loop() {
  curMillis = millis();
  getDataFromPC();
  switchLEDs();
}

void getDataFromPC() {
    // receive data from PC and save it into inputBuffer
  if(Serial.available() > 0) {
    char x = Serial.read();
    if (x == endMarker) {
      readInProgress = false;
      newDataFromPC = true;
      inputBuffer[bytesRecvd] = 0;
      parseData();
    }
    if(readInProgress) {
      inputBuffer[bytesRecvd] = x;
      bytesRecvd ++;
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
  char * strtokIndx; // this is used by strtok() as an index
  strtokIndx = strtok(inputBuffer,","); // get the first part
  ledStatus[0] = atoi(strtokIndx); //  convert to an integer
  strtokIndx = strtok(NULL, ","); // this continues where the previous call left off
  ledStatus[1] = atoi(strtokIndx); 
}
void switchLEDs() {
  for (byte n = 0; n < numLEDs; n++) {
    digitalWrite( ledPin[n], ledStatus[n]);
  }
}
