/*
 * TO-DO LIST
 * 
 * Calibration  thermo pair
 * Diplay (invert + size of font)
 * Menu - 
 * INfo - Temp + stirr
 * Encoder - smooth rotation
 * Serial - software serial overlap
 *
*/
#include <SoftwareSerial.h>

#include <GParser.h>
#include <parseUtils.h>

#include "SPI.h" // necessary library

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

const byte rxPin = A3;
const byte txPin = A2;
SoftwareSerial mySerial (rxPin, txPin);

const int stirON = 7;
const int thermON = 6;

const int stirPin = 10;
const int thermoPin = 9;

unsigned int wiperValue;
String incomingString;

int pulsePin = 8;
int tempPin = A1;

int val = 0;

//encoder connection

volatile unsigned int encoder0Pos = 0;
#define CLK 2
#define DT 3
#define SW 4

int valStir;
int valTemp;


byte chFLAG = 0;
byte menuCount = 1;

int counter = 0;
int currentStateCLK;
int lastStateCLK;
String currentDir ="";
unsigned long lastButtonPress = 0;


//dispay initialization 

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(-1);



int pulseHigh; // Integer variable to capture High time of the incoming pulse
int pulseLow; // Integer variable to capture Low time of the incoming pulse
float pulseTotal; // Float variable to capture Total time of the incoming pulse
float frequency; // Calculated Frequency



void setup() {
  //encoder initialization
  pinMode(CLK,INPUT);
  pinMode(DT,INPUT);
  pinMode(SW, INPUT_PULLUP);


  //display init
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);  
 
  // Read the initial state of CLK
  lastStateCLK = digitalRead(CLK);
  display.clearDisplay();
  
  // Display Text
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0,28);
  display.println("Hello world!");
  display.display();
  delay(2000);
  display.clearDisplay();

  // Begin Serial port and print out welcome message
  mySerial.begin(9600);
  

  //Digital pots initialization
  pinMode(stirPin, OUTPUT);
  pinMode(thermoPin, OUTPUT);
  digitalWrite(stirPin, HIGH);
  digitalWrite(thermoPin, HIGH);

  SPI.begin(); // wake up the SPI bus.
  SPI.setBitOrder(MSBFIRST);

  //heater and stirrer OFF
  pinMode(stirON,OUTPUT);
  pinMode(thermON,OUTPUT);
  digitalWrite(stirON, HIGH);
  digitalWrite(thermON, HIGH);

  //sensors initialization
  pinMode(pulsePin,INPUT);
  pinMode(tempPin,INPUT);

  mySerial.println("RUN");

  
}

void setValue(int pin, int value)
// sends value 'value' to SPI device on CS digital out pin 'l'
{
  digitalWrite(pin, LOW);
  SPI.transfer(0); // send command byte
  SPI.transfer(value); // send value (0~255)
  digitalWrite(pin, HIGH);
  delay(100);
}


///device, code, value;

///DEVICE : 1 - STIRRER ; 2 - THERMO

///code - 1: SET VALUE
///code - 2: READ SENSOR

void freq(){
  pulseHigh = pulseIn(pulsePin,HIGH);
  pulseLow = pulseIn(pulsePin,LOW);
  pulseTotal = pulseHigh + pulseLow; // Time period of the pulse in microseconds
  frequency=1000000/pulseTotal/60;      // Frequency in Hertz (Hz)
  mySerial.print("Frequency  =");
  mySerial.print(frequency);
  mySerial.println(" Hz;");
  delay(300);
  }
void temp(){
  val = analogRead(tempPin);
  mySerial.print(val);
  mySerial.println(" C;");
  delay(300);  
}

void set_speed(int speed){
  if (speed >= 0){
    digitalWrite(stirON, LOW);
    setValue(stirPin,speed);
  } else {
    digitalWrite(stirON, HIGH);
    }
}

void set_temp(int t){
  if (t >= 0){
    digitalWrite(thermON, LOW);
    setValue(thermoPin,t);
    mySerial.println(t);
  } else {
    digitalWrite(thermON, HIGH);
    }
}

void loop() {
  // Read the current state of CLK
  currentStateCLK = digitalRead(CLK);
  
  if (currentStateCLK != lastStateCLK  && currentStateCLK == 1){
    if (digitalRead(DT) != currentStateCLK) {
      if (chFLAG == 0){
        menuCount--;
        if (menuCount < 1){
          menuCount = 3;
        }
      }else{
        switch (menuCount) {
          case 1: {valStir--;break;}
          case 2: {valTemp--;break;}
          case 3: {break;}}
          
      }
     }
     else {
      if (chFLAG == 0){
        menuCount++;
      if (menuCount > 3){
        menuCount = 1;
      }
      currentDir ="CW";
      } else {
        switch (menuCount) {
          case 1: {valStir++;break;}
          case 2: {valTemp++;break;}
          case 3: {break;}}
        
      }
    }
    
    //Serial.print(" | Counter: ");
    //Serial.println(menuCount);
  }

  // Remember last CLK state
  lastStateCLK = currentStateCLK;

  // Read the button state
  int btnState = digitalRead(SW);

  //If we detect LOW signal, button is pressed
  if (btnState == LOW) {
    //if 50ms have passed since last LOW pulse, it means that the
    //button has been pressed, released and pressed again
    if (millis() - lastButtonPress > 500 && chFLAG == 1) {
      chFLAG = 0;
      mySerial.println(chFLAG);       
    } else {
      chFLAG = 1;
      mySerial.println(chFLAG);   
    }

    // Remember last button press event
    lastButtonPress = millis();
  }

  // Put in a slight delay to help debounce the reading
  delay(1);

  staticMenu();
  display.clearDisplay();
  delay(1);
  
 

  
  //Serial protocol
  if (mySerial.available() > 1 ) {
    char buf[50];
    int amount = mySerial.readBytesUntil(';', buf, 15);
    buf[amount] = NULL;
    
    GParser data(buf, ',');
    int ints[2];
    data.parseInts(ints);
  
   
    switch (ints[0]) {
      case 1:
        switch (ints[1]){
          case 1: {set_speed(ints[2]);break;}
          case 2: {freq();break;}
          break;}
        break;

      case 2:
        switch (ints[1]){
          case 1: {set_temp(ints[2]);break;}
          case 2: {temp();break;}
          break;}
        break;
  }
  }
 
}

void staticMenu() {
  display.setTextSize(1);
  display.setTextColor(WHITE);

  display.setCursor(10, 0);
  display.println("Stirrer:");
  display.setCursor(70, 0);
  display.println(valStir);

  display.setCursor(10, 20);
  display.println("Temp:");
  display.setCursor(70, 20);
  display.println(valTemp);

  display.setCursor(10, 40);
  display.println("Info:");
  display.setCursor(70, 40);
  
  display.setCursor(2, (menuCount * 20) -20 );
  display.println(">");

  display.display();
}
