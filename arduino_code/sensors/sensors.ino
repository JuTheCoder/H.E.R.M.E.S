// Necessary libraries
#include <SoftwareSerial.h>
#include <MHZ19.h>

// Sets arduino pin 10 as co2 receiver, pin 11 as co2 transmitter, and A1 as co reader
#define CO2_RX 10
#define CO2_TX 11
#define MQ2_PIN A1

MHZ19 co2Sensor;
// Sets up a separate communication channel for arduino and co2 sensor
SoftwareSerial co2Serial(CO2_RX, CO2_TX);

void setup() {
    // Uses standard baud rate of 9600 for communication 
    Serial.begin(9600);
    co2Serial.begin(9600);
    co2Sensor.begin(co2Serial);
    
    // Explicitly sets A1 as an input to read voltage
    pinMode(MQ2_PIN, INPUT);
}

void loop() {
    static unsigned long timer = 0;

    // Checks if timer has reached 2 seconds
    if (millis() - timer >= 2000) {
        // Reads the co2 sensor level
        int co2 = co2Sensor.getCO2();
        
        // Reads the co sensor level
        int mq2 = analogRead(MQ2_PIN);

        // Format for the Raspberry Pi/Serial Monitor output
        Serial.print(co2);
        Serial.print(",");
        Serial.println(mq2);

        // restarts timer
        timer = millis();
    }
}
