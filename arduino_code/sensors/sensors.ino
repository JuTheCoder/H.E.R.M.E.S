#include <SoftwareSerial.h>
#include <MHZ19.h>
#include <LiquidCrystal.h>
#include <DHT.h>

// Pin Definitions
#define CO2_RX 10       // CO2 Sensor RX uses pin 10
#define CO2_TX 11       // CO2 Sensor TX uses pin 11
#define MQ2_PIN A5      // CO sensor uses Arduino pin A5
#define MQ135_PIN A0    // Air Quality sensor uses Arduino pin A0
#define DHT_PIN 7       // Temperature pin uses pin 7
#define DHT_TYPE DHT22  // Temperature sensor variable

// Object Initialization
LiquidCrystal screen(12, 8, 5, 4, 3, 2); 
MHZ19 co2Sensor;
SoftwareSerial co2Serial(CO2_RX, CO2_TX);
DHT dht(DHT_PIN, DHT_TYPE); 

void setup() {
    Serial.begin(9600);           // Raspberry Pi Communication
    co2Serial.begin(9600);        // CO2 Sensor Communication
    co2Sensor.begin(co2Serial);   // Starts CO2 sensor
    dht.begin();                  // Starts Temperature sensor
    
    pinMode(LED_BUILTIN, OUTPUT);
    screen.begin(16, 2);          // Starts lcd
    screen.clear();
    
    // Set-up sequence
    screen.print("Initializing sensor display...");
    screen.setCursor(0, 1);
    delay(3000); 
}

void loop() {
    // 1. Collect Data from all 4 sensors
    int co2_mh = co2Sensor.getCO2(); 
    int co_mq2 = analogRead(MQ2_PIN);
    int aq_mq135 = analogRead(MQ135_PIN); 
    float tempF = dht.readTemperature(true); // Passed true to set temp to Fahrenheit

    // 2. Calculate Air Quality % from MQ-135
    // Adjust 100/600 based on your specific outdoor baseline (will set outdoor baseline later)
    int aq_score = map(aq_mq135, 100, 600, 0, 100);
    aq_score = constrain(aq_score, 0, 100);

    // 3. Update LCD with sensor values
    screen.clear();
    
    // Top Row: CO2 and Temperature values
    screen.setCursor(0, 0);
    screen.print("C2:"); screen.print(co2_mh);
    
    screen.setCursor(9, 0); 
    screen.print("T:"); screen.print(tempF, 0); screen.print("F");

    // Bottom Row: Air Quality % and CO values
    screen.setCursor(0, 1);
    screen.print("AQ:"); screen.print(aq_score); screen.print("%");
    
    screen.setCursor(9, 1); 
    screen.print("CO:"); screen.print(co_mq2);

    // 4. Send CSV Data to Raspberry Pi
    // Format: CO2,CO,AQ,TempF
    Serial.print(co2_mh); Serial.print(",");
    Serial.print(co_mq2); Serial.print(",");
    Serial.print(aq_mq135); Serial.print(",");
    Serial.println(tempF);

    // Total loop timing: ~3 seconds
    delay(3000); 
}
