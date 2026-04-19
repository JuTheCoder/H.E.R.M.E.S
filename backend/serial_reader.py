"""
serial_reader.py
"""
import json
import serial
import requests

# Port for the Arduino and the Baud Rate
SERIAL_PORT = "/dev/cu.usbmodem101"
BAUD_RATE = 9600

# Post endpoint that'll send the data to our API
API_URL = "http://127.0.0.1:8000/api/sensor-data"

# Opens up a pipeline to the Arduino 
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

print("Listening to Arduino...")

while True:
    try:
        # Serial format that is turned into actual readable text and then white spaces are taken out
        line = ser.readline().decode('utf-8').strip()
        # Loops back to the top of the while loop to ignore any empty lines
        if not line:
            continue

        # Actual string that is sent by the Arduino
        print("Raw: ", line)

        # Convert JSON string to dictionary
        data = json.loads(line)

        # Maps the data we actually need to the SensorReading format that our Post endpoint will use
        payload = {
            "co2": data["co2"],
            "co": data["co"],
            "air": data["aq_percent"],   
            "temperature": data["temperature"]
        }

        print("Sending: ", payload)

        # Calling our Post endpoint and send the data to our API
        response = requests.post(API_URL, json=payload, timeout=10)

        # Confirmation that the data was sent to our API (200 = Successful)
        print("Sent to API: ", response.status_code)
        print("Response:", response.text)

    # Error handling
    except json.JSONDecodeError:
        print("Invalid JSON, skipping...")
    except Exception as e:
        print("Error: ", e)
