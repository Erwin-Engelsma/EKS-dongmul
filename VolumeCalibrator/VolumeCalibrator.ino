/* Valve control */
#define Open 1
#define Close 0

/* Soft Robot hardware settings */
int vacuumPump = 10;
int pressurePump = 11;
const int Valve1 = 4;
const int Valve2 = 5;
const int Valve3 = 6;

int PWMPump = 110; // PWM to the motors
int command = 0; // defines what to do
/* Communication */
char initialized = 'i';
bool stopMeasurement = false; // used to stop a measurement if some condition is met.

/* Timing parameters */
long int sampleTime = 250; // default 4 samples per second are take, can be adapted
long int startTime = 0; // for the admin of sampletimes
long int logTime = 0; // used to log the time at which a sample was taken relative to start
long int nextSampleTime = 0; //Used to tell if the next sample must be taken

/* pressure control */
int currentPressure = 0; // Pressure as read from the sensor
int previousPressure = 0; // used to check the change in pressure
int pressureThreshold = 528; // above this pressure a decrease in pressure stops the measurement
int vacuumThreshold = 513; // Vacuumpump stops when pressure gets below this pressure
int maxPressure = 530; // Pumping stops when this pressure is reached


/* 
 *  Via command followed by three ints the values are set
 */
void setPressureThresholds(){
  pressureThreshold = Serial.parseInt();
  vacuumThreshold = Serial.parseInt();
  maxPressure = Serial.parseInt();  
}

/* 
 *  Via command followed by two ints the values are set
 *  It returns the set params to caller
 */
void setMoveParams(){
    PWMPump = Serial.parseInt(); 
    sampleTime = Serial.parseInt();  
}

  /*
   * stop pumps and empty.
   * May be used as 'emergency measure', control from Python is possible!
   */
void resetVolume(){
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
/*
 * If time is up report currentpressure and set next reporting time
 */
void printInfo(bool force = false){
    if (millis() > nextSampleTime || force == true) { 
    nextSampleTime += sampleTime;
    logTime = millis() - startTime;
    Serial.print(logTime );
    Serial.print(' '); 
    Serial.print(currentPressure);
    Serial.print('\n');   
  }
}

/*
 * Pump up to full volume and measure emptying behaviour
 */
void measureLeakage(){
  stopMeasurement = false;
  readPressure();
  startTime = millis();
  nextSampleTime = startTime;
  while (not stopMeasurement){
    if (Serial.available()){
      char a = Serial.read();
      if (a == '3'){
        stopMeasurement = true;
        resetVolume();
        Serial.print("U\n");       
      }
    } 
    if (currentPressure < vacuumThreshold){
      Serial.print("V\n");
      resetVolume();
      stopMeasurement = true;
    } 
    readPressure();
    printInfo();
  }
}

void readPressure(){
    currentPressure = analogRead(A3);   
}
/*
 * Measure time to reach 'vacuum' assuming a fully blown muscle
 */
void measureVacuum(bool logThis = false){
  stopMeasurement = false;
  readPressure();
  startTime = millis();
  nextSampleTime = startTime;
  analogWrite(pressurePump, 0);
  analogWrite(vacuumPump, PWMPump);
  while (not stopMeasurement){
    readPressure(); 
    if (Serial.available()){
      char a = Serial.read();
      if (a == '!'){
        stopMeasurement = true;
        analogWrite(pressurePump, 0);
        resetVolume();
        Serial.print("U\n");       
      }
    } 
    if (logThis) {
      printInfo();
    }
    if (currentPressure <= vacuumThreshold){
      printInfo();
      Serial.print("V\n");
      resetVolume();
      stopMeasurement = true;
    }  
  }
}

/* Measure the pumping action of filling the muscle */
void measurePressure(bool logThis = false){
  stopMeasurement = false;
  Serial.print("MP, ");
  Serial.print(PWMPump);
  Serial.print('\n');
  previousPressure = currentPressure;
  readPressure(); 
  startTime = millis();
  nextSampleTime = startTime;
  analogWrite(vacuumPump, 0);
  analogWrite(pressurePump, PWMPump);
  while (not stopMeasurement){
    previousPressure = currentPressure;
    delay(15);
    readPressure();  
    delay(10); 
    if (logThis){
      printInfo();  
    }
    if (Serial.available()){
      char a = Serial.read();
      if (a == '!'){
        stopMeasurement = true;
        analogWrite(pressurePump, 0);
        resetVolume();
        Serial.print("U\n");       
      }
    }    
    if (currentPressure > maxPressure){
      Serial.print("P\n");
      //resetVolume();
      stopMeasurement = true;
    }
    if (currentPressure < previousPressure && currentPressure > pressureThreshold){
      printInfo(true);
      stopMeasurement = true;
    }  
  } 
  analogWrite(pressurePump, 0);
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
  /* clean buffer for any accidental bytes*/
  while (Serial.available()) {
      Serial.read();
    }
  analogWrite(vacuumPump, 0);
  /* Signal that Arduino is ready */
  Serial.print("i\n"); 

  /* Wait for data to be sent to Arduino */
  while (not Serial.available()){
    delay(10);
  }
}
/*
 * Commands that can be given:
 * 0: set the movement parameters, for PWM and sampletime
 * 1: Do full measurement cycle of pressurizing and depressurizing
 * 2: Do leakage measurement, pressurize and measure time to empty
 * 3: Set pressure parameters (ints): pressureThreshold vacuumThreshold maxPressure
 */
void loop() {
  if (Serial.available()){
    command = Serial.parseInt();
    if (command == 0){
      setMoveParams();       
      Serial.print("MP \n"); 
    }
    if (command == 1){
      resetVolume();
      measurePressure();
      measureVacuum();      
      Serial.print("MC \n");
    }
    if (command == 2){
      resetVolume();
      measurePressure();  
      measureLeakage();   
      Serial.print("MC \n");
    }
    if (command == 3){
      setPressureThresholds();
    }
    if (command == 4){
      resetVolume();
      measurePressure(true);
      measureVacuum(true);      
      Serial.print("MC \n");
    }
  }
}
  
