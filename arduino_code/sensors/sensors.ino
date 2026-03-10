#include <SoftwareSerial.h>
#include <MHZ19.h>
#include <LiquidCrystal.h>
#include <DHT.h>

// Pin Definitions
#define CO2_RX 10        
#define CO2_TX 11        
#define MQ2_PIN A5       
#define MQ135_PIN A0     
#define DHT_PIN 7        
#define DHT_TYPE DHT22   

// Configuration
#define READ_INTERVAL 3000  // 3 seconds between sensor reads
#define BAUD_RATE 9600      // Serial baud rate for Raspberry Pi

// Object Initialization
LiquidCrystal screen(12, 8, 5, 4, 3, 2); 
MHZ19 co2Sensor;
SoftwareSerial co2Serial(CO2_RX, CO2_TX);
DHT dht(DHT_PIN, DHT_TYPE); 

// Timing 
unsigned long lastReadTime = 0;

void setup() {
    Serial.begin(BAUD_RATE);      // Communication with Raspberry Pi
    co2Serial.begin(9600);        // Communication with CO2 Sensor
    co2Sensor.begin(co2Serial);   
    dht.begin();                  
    
    pinMode(LED_BUILTIN, OUTPUT);
    screen.begin(16, 2);          
    screen.clear();
    
    screen.print("H.E.R.M.E.S. Init");
    screen.setCursor(0, 1);
    screen.print("Warm-up: 30s...");
    
    // 30 second warm-up for MQ sensors as per H.E.R.M.E.S requirements
    delay(30000); 
    screen.clear();
}

void loop() {
    unsigned long currentTime = millis();

    // Non-blocking timer check
    if (currentTime - lastReadTime < READ_INTERVAL) {
        return;
    }
    lastReadTime = currentTime;

    // 1. Collect Data
    int co2_mh = co2Sensor.getCO2(); 
    int co_mq2 = analogRead(MQ2_PIN);
    int aq_mq135 = analogRead(MQ135_PIN); 
    float tempF = dht.readTemperature(true);
    float humidity = dht.readHumidity();

    // 2. Error Check for DHT22
    if (isnan(tempF) || isnan(humidity)) {
        Serial.println("{\"error\": \"DHT22 Read Failed\"}");
        return; 
    }

    // 3. Process MQ-135 Score (0-100%)
    int aq_score = map(aq_mq135, 100, 600, 0, 100);
    aq_score = constrain(aq_score, 0, 100);

    // 4. Update LCD Display
    screen.clear();
    // Row 0: CO2 and Temp
    screen.setCursor(0, 0);
    screen.print("C2:"); screen.print(co2_mh);
    screen.setCursor(9, 0); 
    screen.print("T:"); screen.print(tempF, 0); screen.print("F");

    // Row 1: AQ% and CO
    screen.setCursor(0, 1);
    screen.print("AQ:"); screen.print(aq_score); screen.print("%");
    screen.setCursor(9, 1); 
    screen.print("CO:"); screen.print(co_mq2);

    // 5. Send JSON Data to Raspberry Pi
    Serial.print("{");
    Serial.print("\"co2\":");         Serial.print(co2_mh);
    Serial.print(",\"co_mq2\":");     Serial.print(co_mq2);
    Serial.print(",\"mq135_raw\":");  Serial.print(aq_mq135);
    Serial.print(",\"aq_percent\":"); Serial.print(aq_score);
    Serial.print(",\"temp_f\":");     Serial.print(tempF, 1);
    Serial.print(",\"humidity\":");   Serial.print(humidity, 1);
    Serial.println("}");
}
