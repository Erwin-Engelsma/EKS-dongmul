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

int PWMPump = 140; // PWM to the motors
int command = 0;
/* Communication */
char initialized = 'i';
bool stopMeasurement = false;

/* Timing parameters */
long int sampleTime = 250;
long int startTime = 0;
long int logTime = 0;
long int nextSampleTime = 0;

/* pressure control */
int currentPressure = 0;
int previousPressure = 0;
int detectionThreshold = 525;
int maxPressure = 530;

void setParameters(){
    PWMPump = Serial.parseInt(); 
    sampleTime = Serial.parseInt();  
    Serial.print('\n');
    Serial.print('p');
    Serial.print(PWMPump);
    Serial.print('t');  
    Serial.print(sampleTime);
    Serial.print('\n');
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

  // Set for control by pumps:
  digitalWrite (Valve1, Close); 
  digitalWrite (Valve2, Close);
  digitalWrite (Valve3, Open);
}

void printInfo(){
  Serial.print(logTime);
  Serial.print(':'); 
  Serial.print(currentPressure);
  Serial.print('\n');
}

/* Actual move execution */
void doMeasurement(){
  stopMeasurement = false;
  Serial.print("\nPWM:");
  Serial.print(PWMPump);
  Serial.print('\n');
  
  currentPressure = analogRead(A3); 
  previousPressure = currentPressure;
  startTime = millis();
  nextSampleTime = startTime;

  while (not stopMeasurement){
    if (Serial.available()){
      char a = Serial.read();
      if (a == '3'){
        stopMeasurement = true;
        analogWrite(pressurePump, 0);
        resetVolume();
        Serial.print("User stopped measurement \n");       
      }
    }    
    if (currentPressure > maxPressure){
      printInfo();
      Serial.print("Pressure exceeded \n");
      resetVolume();
      stopMeasurement = true;
    }
    if (currentPressure<previousPressure && currentPressure > detectionThreshold){
      printInfo();
      Serial.print("Pressure dropped \n");
      resetVolume();
      stopMeasurement = true;
    }    
    if (millis() > nextSampleTime) {
      previousPressure = currentPressure;
      currentPressure = analogRead(A3); 
      nextSampleTime += sampleTime;
      logTime = millis() - startTime;
      printInfo();    
    } 
  } 
} 

void setup() {
  Serial.begin(115200);
  pinMode (A3, INPUT);
  pinMode(vacuumPump, OUTPUT);
  pinMode(pressurePump, OUTPUT);
  pinMode(Valve1, OUTPUT);
  pinMode(Valve2, OUTPUT);
  pinMode(Valve3, OUTPUT);
  
  resetVolume();
  /* clean buffer */
  while (Serial.available()) {
      Serial.read();
    }
  analogWrite(vacuumPump, 0);
  /* Signal that Arduino is ready */
  Serial.print(initialized); 

  /* Wait for data to be sent to Arduino */
  while (not Serial.available()){
    delay(10);
  }
  delay(10);  // sloppy way to make sure all data is in, good enough for hack program
}

void loop() {
  if (Serial.available()){
    command = Serial.parseInt();
    if (command == 0){
      setParameters();   
    }
    if (command == 1){
      resetVolume();
      analogWrite(pressurePump, PWMPump);
      delay(500); // Wait till inflation has really begun
      doMeasurement();
    }
    if (command == 2){
      resetVolume();
    }
  }
}
  
