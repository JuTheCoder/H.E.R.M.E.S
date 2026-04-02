import serial 
import json
import requests

SERIAL_PORT = "/dev/cu.usbmodem1101"
BAUD_RATE = 9600

API_URL = "http://127.0.0.1:8000/api/sensor-data"

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

print("Listening to Arduino..")

while True:
    try:
        line = ser.readline().decode('utf-8').strip()

        if not line:
            continue

        print("Raw: ", line)

        data = json.loads(line) # Convert JSON string to dictionary 

        payload = {
            "co2": data["co2"],
            "co": data["co_mq2"],
            "air": data["aq_percent"],   
            "temperature": data["temp_f"]
        }

        print("Sending: ", payload)

        response = requests.post(API_URL, json=payload)

        print("Sent to API: ", response.status_code)
        print("Response:", response.text)

    except json.JSONDecodeError:
        print("Invalid JSON, skipping...")
    except Exception as e:
        print("Error: ", e)