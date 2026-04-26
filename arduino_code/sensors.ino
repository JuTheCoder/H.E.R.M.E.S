/*
  H.E.R.M.E.S. - Main Sensor Collection Script
  Reads from DHT22, MQ135, MQ2, and MH-Z19 sensors
  Sends JSON data over serial to the Raspberry Pi
  Shows readings on the LCD and triggers alerts if something's off

  Pins are mapped out in the defines below -
  double check these match your actual wiring before uploading
*/

#include <SoftwareSerial.h>
#include <MHZ19.h>
#include <LiquidCrystal.h>
#include <DHT.h>

// --- Sensor Pins ---
#define CO2_RX 10          // MH-Z19 receive pin
#define CO2_TX 11          // MH-Z19 transmit pin
#define MQ2_PIN A5         // MQ2 gas sensor (CO detection)
#define MQ135_PIN A0       // MQ135 air quality sensor
#define DHT_PIN 7          // DHT22 temp/humidity sensor
#define DHT_TYPE DHT22

// --- Alert Pins ---
#define ALERT_LED 6        // Red LED for danger warnings
#define BUZZER_PIN 9       // Buzzer for audio alerts

// --- Settings ---
#define READ_INTERVAL 3000 // How often we read sensors (3 seconds)
#define BAUD_RATE 9600     // Serial speed for Pi communication
#define CO2_DANGER 3000    // CO2 level that triggers an alert (ppm)
#define TEMP_DANGER 95     // Temperature that triggers an alert (F)
#define CO_DANGER 850      // MQ2 raw value that triggers alert
#define AQ_DANGER 70       // air quality % that triggers alert

// --- Setup our hardware objects ---
LiquidCrystal screen(12, 8, 5, 4, 3, 2);  // LCD pins: RS, E, D4, D5, D6, D7
MHZ19 co2Sensor;
SoftwareSerial co2Serial(CO2_RX, CO2_TX);
DHT dht(DHT_PIN, DHT_TYPE);

// Keeps track of when we last grabbed a reading
unsigned long lastReadTime = 0;

void setup() {
    Serial.begin(BAUD_RATE);
    co2Serial.begin(9600);
    co2Sensor.begin(co2Serial);
    dht.begin();

    pinMode(ALERT_LED, OUTPUT);
    pinMode(BUZZER_PIN, OUTPUT);

    screen.begin(16, 2);
    screen.clear();

    // Give the sensors 30 seconds to warm up before we start reading
    screen.print("H.E.R.M.E.S.");
    screen.setCursor(0, 1);
    screen.print("Warming up...");

    delay(30000);
    screen.clear();
}

void loop() {
    unsigned long now = millis();

    // Only read every READ_INTERVAL milliseconds
    if (now - lastReadTime < READ_INTERVAL) {
        return;
    }
    lastReadTime = now;

    // -- Grab all the sensor readings --
    int co2_val = co2Sensor.getCO2();
    int co_raw = analogRead(MQ2_PIN);
    int aq_raw = analogRead(MQ135_PIN);
    float tempF = dht.readTemperature(true);  // true = Fahrenheit
    float humidity = dht.readHumidity();

    // If the DHT22 gives us garbage, skip this cycle
    if (isnan(tempF) || isnan(humidity)) {
        Serial.println("{\"error\": \"DHT22 read failed\"}");
        return;
    }

    // Turn the raw MQ135 value into a 0-100% score
    // 100 = clean air baseline, 600 = pretty bad
    int aq_score = map(aq_raw, 100, 600, 0, 100);
    aq_score = constrain(aq_score, 0, 100);

    // -- Check if we need to sound the alarm --
    bool danger = (co2_val > CO2_DANGER || tempF > TEMP_DANGER || co_raw > CO_DANGER || aq_score > AQ_DANGER);

    if (danger) {
        digitalWrite(ALERT_LED, HIGH);
        tone(BUZZER_PIN, 1500, 300);
    } else {
        digitalWrite(ALERT_LED, LOW);
        noTone(BUZZER_PIN);
    }

    // -- Update the LCD screen --
    screen.clear();

    // Top row: CO2 and Temperature
    screen.setCursor(0, 0);
    screen.print("C2:");
    screen.print(co2_val);
    screen.setCursor(9, 0);
    screen.print("T:");
    screen.print(tempF, 0);
    screen.print("F");

    // Bottom row: alert message or AQ/CO readings
    screen.setCursor(0, 1);
    if (danger) {
        screen.print("!! ALERT !!");
    } else {
        screen.print("AQ:");
        screen.print(aq_score);
        screen.print("%");
        screen.setCursor(9, 1);
        screen.print("CO:");
        screen.print(co_raw);
    }

    // -- Send everything to the Pi as JSON --
    // These field names match what serial_reader.py expects
    Serial.print("{");
    Serial.print("\"co2\":");          Serial.print(co2_val);
    Serial.print(",\"co\":");          Serial.print(co_raw);
    Serial.print(",\"aq_percent\":");  Serial.print(aq_score);
    Serial.print(",\"temperature\":"); Serial.print(tempF, 1);
    Serial.println("}");
}
