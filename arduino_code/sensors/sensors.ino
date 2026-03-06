/*
 * H.E.R.M.E.S. - Sensor Module
 * DHT22 (Temperature/Humidity) + MQ135 (Air Quality/CO2)
 * Board: Arduino Uno/Nano
 *
 * REQUIRED LIBRARIES (install via Arduino IDE Library Manager):
 *   - "DHT sensor library" by Adafruit
 *   - "Adafruit Unified Sensor" by Adafruit
 *
 * WIRING:
 *   DHT22:  VCC to 5V | GND to GND | DATA to D2
 *   MQ135:  VCC to 5V | GND to GND | AO   to A1
 *
 * NOTE: MQ135 needs ~2 min warm-up each power cycle (24-48 hrs on first use).
 *       DHT22 needs ~2 sec between reads.
 */

#include <DHT.h>

//Pin Definitions
#define DHT_PIN     2       // Digital pin for DHT22 data line
#define MQ135_PIN   A1      // Analog pin for MQ135 analog output
#define DHT_TYPE    DHT22   // Sensor type (DHT22 / AM2302)

//Configuration
#define READ_INTERVAL 2000  // Milliseconds between readings (DHT22 min = 2000)
#define BAUD_RATE    9600   // Serial baud rate - must match Python side

// Sensor Object
DHT dht(DHT_PIN, DHT_TYPE);

// Timing 
unsigned long lastReadTime = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  dht.begin();

  // Give MQ135 some warm-up time
  Serial.println("H.E.R.M.E.S. Sensor Module Starting...");
  Serial.println("Waiting 30 seconds for MQ135 warm-up...");
  delay(30000);  // 30 sec warm-up (increase for better accuracy)
  Serial.println("Warm-up complete. Beginning readings.");
  Serial.println("---");
}

void loop() 
{
  unsigned long currentTime = millis();

  // Only read every READ_INTERVAL milliseconds
  if (currentTime - lastReadTime < READ_INTERVAL) {
    return;
  }
  lastReadTime = currentTime;

  // Read DHT22
  float humidity    = dht.readHumidity();
  float tempC       = dht.readTemperature();       // Celsius
  float tempF       = dht.readTemperature(true);    // Fahrenheit

  // Check for failed DHT22 read
  if (isnan(humidity) || isnan(tempC) || isnan(tempF)) {
    Serial.println("ERROR: DHT22 read failed. Check wiring.");
    return;
  }

  // Read MQ135 
  int mq135Raw = analogRead(MQ135_PIN);  // Raw value 0-1023

  // Convert MQ135 raw to voltage (for reference/debugging)
  float mq135Voltage = mq135Raw * (5.0 / 1023.0);

  // Output as JSON for Python to parse 
  Serial.print("{");
  Serial.print("\"temperature\":");   Serial.print(tempF, 1);
  Serial.print(",\"humidity\":");     Serial.print(humidity, 1);
  Serial.print(",\"mq135_raw\":");    Serial.print(mq135Raw);
  Serial.print(",\"mq135_voltage\":"); Serial.print(mq135Voltage, 2);
  Serial.println("}");
}
