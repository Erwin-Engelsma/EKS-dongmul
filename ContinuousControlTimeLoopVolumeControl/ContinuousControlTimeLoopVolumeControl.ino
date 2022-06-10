#include <MapFloat.h>

/* Valve control */
#define Open 1
#define Close 0

/* Soft Robot hardware settings */
int vacuumPump = 10;
int pressurePump = 11;
const int Valve1 = 4;
const int Valve2 = 5;
const int Valve3 = 6;

/* Pressure controls 
   Assumed is:
   1) with equal pressure motor rotation speed is linear with PWM,with an offset  (motRot = factor * (PWM - floor) )
   2) with increasing pressure, motor rotation is linearly influenced (faster or slower depending on vacuum or pressure motor
   2a) pressure is assumed 0 at 500 sensor reading
   3) Pressurepump: deltaVolume = integrateTime * (PWMPump - floor) * pressureDeltaVolume * pressureZero / currentPressure
   4) Vacuumpump:   deltaVolume = - integrateTime * (PWMPump - floor)* vacuumDeltaVolume * currentPressure / pressureZero
   5) Leakage in the tubes can be neglected (no idea if this is true)
   Note for 3 and 4: higher pressure slows pressure pump down and speeds vacuumpump up
   Note for 3 and 4: vacuumpump gets out air much faster than pressurepump gets air in
   Note for all above: these are guesses, and should be measured and calibrated, or real volume should be measured
   Measuring real calibrated air flow is preferred.
   Note the algorithms were made with some educated guessing and tinkering. I have not checked if they can be made 
   more efficient. E.g. by calculating 'constants' only once or by checking if multiplying int and float is faster than 
   casting int to float and then multiplying. So still some evaluation to be done.
   Also: measuring real air displacement is better.
*/

int PWMPump = 0; // PWM to the motors, pump rotation speed assumed to be linear with PWM at 0 counterpressure
float setVolume = 0.0;         // Requested volume of air in Dongmul 
float currentVolume = 0.0;     // Current 'calcuguessed' volume of air in Dongmul, prefer using a sensor
float pressureZero = 500; // Atmosphere pressure is roughly 500 by the factor with currentpressure a linear relation is assumed
float currentPressure = 500;   // Current pressure as measured by presssure sensor
float maxVolume = 2500.0;   // max Allowed volume
int basePressure = 0; // base line calibration for low pressure, used to stop vacuumpump when dongmul is empty

/* Communication */
int thisCommand = 0;
float firstFloat = 0; // First float number that enters in the comm protocol
float secondFloat = 0; // Second float number that enters in the comm protocol
char initialized = 'i';

/* Timing parameters */
long int moveTime = 0; // Determines the time that the next movement is made must be long (mSec)
long int nextMoveTime = 300; // time in mSec before next move is made after completion.
//float integrateTime = float(nextMoveTime) / 1000.0; // integration time for calculating the pumped air volume, in Seconds
long int reportPressureTime = 0; //Timer for next time to report air pressure
long int nextReportPressureTime = 1000; //Delay in reporting next pressure, in mSec

/* send the measured pressure to Python */
void reportPressure(){
    reportPressureTime = millis() + nextReportPressureTime;
    currentPressure = analogRead(A3);   
    Serial.print("Press, Volume: ");
    Serial.print(currentPressure);
    Serial.print(" ");
    Serial.print(currentVolume);    
}

void calibrateVolume(){
//    pressureDeltaVolume = Serial.parseFloat(); 
//    vacuumDeltaVolume = Serial.parseFloat();      
}

void executeCommand(){
    firstFloat = Serial.parseFloat(); 
    secondFloat = Serial.parseFloat(); 
    PWMPump = mapFloat(firstFloat, 0, 1, 65, 110);
    setVolume = mapFloat(secondFloat, 0, 1, 0, maxVolume);       
}

void resetVolume(){
  /*
   * stop pumps and empty.
   * May be used as 'emergency measure', control from Python is possible!
   */
  analogWrite(vacuumPump, 0);
  analogWrite(pressurePump, 0);
    /* Set for emptying out air */
  digitalWrite (Valve1, Open); 
  digitalWrite (Valve2, Open);
  digitalWrite (Valve3, Close);
  delay (2000); // Wait for all mechanical action to finish
  basePressure = analogRead(A3) ; // measure and provide the base pressure  
  currentVolume = 0;
  // Set for control by pumps:
  digitalWrite (Valve1, Close); 
  digitalWrite (Valve2, Close);
  digitalWrite (Valve3, Open);
}

/* Actual move execution */
void doTheMove(){
    moveTime = millis() + nextMoveTime; // put here so duration of calculation does not influence it
    currentPressure = analogRead(A3);
   
    /* If currentVolume smaller than set Volume,  then: Inflate else deflate (if pressure high enough)
     */
    if (currentVolume < setVolume && currentPressure <= 530) {
      analogWrite(vacuumPump, 0);
      analogWrite(pressurePump, PWMPump);
      currentVolume += PWMPump * (nextMoveTime * 0.010023 - 0.59826);
      
    } else {  
      if (currentPressure > 515) {  // basePressure
        analogWrite(vacuumPump, PWMPump);
        analogWrite(pressurePump, 0); 
        currentVolume -= PWMPump * (nextMoveTime * 0.006065 - 0.34273); 
      }  else{
         analogWrite(vacuumPump, 0); //stop taking air out when pressure below basePressure  
         currentVolume -= nextMoveTime * 0.0001 ;      
      }
    } 
} 

void processTheInput(){
    thisCommand = Serial.parseInt();
    // careful, if times are too short then not all commands may be carried out anymore
    switch (thisCommand) {
      case 0:
        executeCommand();
        break;
      case 1:
       calibrateVolume();
        break;
      case 2:
        resetVolume();  
      default:
        break;
    }
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(500);
  pinMode (A3, INPUT);
  pinMode(vacuumPump, OUTPUT);
  pinMode(pressurePump, OUTPUT);
  pinMode(Valve1, OUTPUT);
  pinMode(Valve2, OUTPUT);
  pinMode(Valve3, OUTPUT);
  
  resetVolume();
  /* Signal that Arduino has started to Python program, and remove any bytes that 
     during startup spikes might have entered the serial pipeline */
  Serial.print(initialized); 
  while (Serial.available()) {
      Serial.read();
    }
}

void loop() {
  if (Serial.available()) {
    processTheInput();
  }
  if (millis() > moveTime){
    doTheMove();
  }  
  if (millis() > reportPressureTime) {
    reportPressure();
  }

}
  
