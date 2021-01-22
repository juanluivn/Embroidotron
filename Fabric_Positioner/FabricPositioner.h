/*    Fabric positioner class     */

#ifndef FabricPositioner_h
#define FabricPositioner_h

#include "Arduino.h"
#include <AccelStepper.h>

class FabricPositioner
{
  public:
    // Constructor
    FabricPositioner(float r1, float r2);

    // Set public variables
    int max_Speed;
    int max_Accel;

    // Set public functions
    boolean isMoving();
    boolean isFinishedMoving();
    void move_To(float x, float y);
    void STOP();
    int getTotalMoves();
    void currentMotorPositions();
    void setupSteppers(); //set speeds and other bits
  private:
    // Set private variables
    int motionState;
    float R1;
    float R2;
    float Dir1;
    float Dir2;
    int totalMoves;

    // Set motor instances
    AccelStepper stepper_x;
    AccelStepper stepper_y;

    // Set private functions
//    void setupSteppers(); //set speeds and other bits
};
#endif
