#include <SoftwareSerial.h>
#include <MHZ19.h>
#include <LiquidCrystal.h>

#define CO2_RX 10 // Arduino listens to co2 sensor on pin 10
#define CO2_TX 11 // Arduino talks to co2 sensor on pin 11 
#define co_pin A5

// Configures the LCD with its Control (12, 8) and Data (5, 4, 3, 2) pins
LiquidCrystal screen(12, 8, 5, 4, 3, 2); 
MHZ19 co2Sensor;

// Links the SoftwareSerial logic to co2 sensor pins
SoftwareSerial co2Serial(CO2_RX, CO2_TX);

void setup() {
    Serial.begin(9600);
    co2Serial.begin(9600); // Starts the software communication at the sensor's required speed
    co2Sensor.begin(co2Serial); // Tells the MHZ19 library which serial port to use
    
    pinMode(LED_BUILTIN, OUTPUT);
    screen.begin(16, 2); // Indicates the screen has 16 columns and 2 rows
    screen.clear();
    
    delay(2000); // Wait 2 seconds to allow sensor heaters to stabilize
}

void loop() {
    
    // Gets co2 and co levels from respective sensors
    int co2 = co2Sensor.getCO2(); 
    int co = analogRead(co_pin);

    // Displays data on lcd
    screen.setCursor(0, 0);
    screen.print("CO2: "); screen.print(co2); screen.print("    ");
    screen.setCursor(0, 1);
    screen.print("CO: "); screen.print(co); screen.print("    ");

    // Sends data to the raspberry pi
    Serial.print(co2); Serial.print(","); Serial.println(co);

    delay(3000); // Waits 3 seconds before getting the next set of levels
}
