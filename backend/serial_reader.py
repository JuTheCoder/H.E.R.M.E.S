"""
Serial Reader - Sits between the Arduino and the API.
Reads JSON data from the Arduino over USB serial,
cleans it up, and POSTs it to the FastAPI backend.

Run this on the Raspberry Pi while the API server is also running.
Usage: python3 serial_reader.py
"""

import serial
import json
import requests
import time
import sys
import urllib3

# shut up the SSL warning since we're using a self-signed cert on localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -- Config --
# This is the USB port the Arduino shows up as on the Pi
# On Mac it's usually /dev/cu.usbmodem101
# On Raspberry Pi it's usually /dev/ttyUSB0 or /dev/ttyACM0
SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 9600
API_URL = "https://127.0.0.1:8000/api/sensor-data"

# How many times to retry if the serial port isn't available
MAX_RETRIES = 10
RETRY_DELAY = 3  # seconds between retries


def find_serial_port():
    """
    Try a few common port names.
    Different systems name them differently.
    """
    possible_ports = [
        "/dev/ttyUSB0",      # Pi with USB adapter
        "/dev/ttyACM0",      # Pi direct connection
        "/dev/ttyACM1",
        "/dev/cu.usbmodem101",  # Mac
        "/dev/cu.usbmodem1101",
        "/dev/cu.usbmodem14101",
    ]

    for port in possible_ports:
        try:
            test = serial.Serial(port, BAUD_RATE, timeout=1)
            test.close()
            print(f"Found Arduino on {port}")
            return port
        except (serial.SerialException, OSError):
            continue

    return None


def connect_serial():
    """Try to open the serial connection, with retries."""
    for attempt in range(MAX_RETRIES):
        port = find_serial_port()
        if port:
            try:
                ser = serial.Serial(port, BAUD_RATE, timeout=2)
                print(f"Connected to Arduino on {port}")
                time.sleep(2)  # give the Arduino a sec to reset
                return ser
            except serial.SerialException as e:
                print(f"Couldn't open {port}: {e}")

        print(f"Retry {attempt + 1}/{MAX_RETRIES} in {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)

    print("Couldn't find the Arduino. Check your USB cable.")
    sys.exit(1)


def send_to_api(payload):
    """POST the sensor data to our FastAPI backend."""
    try:
        response = requests.post(API_URL, json=payload, timeout=5, verify=False)
        if response.status_code == 200:
            print(f"  -> Sent to API OK")
        else:
            print(f"  -> API returned {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        print("  -> API not running? Can't connect to", API_URL)
    except Exception as e:
        print(f"  -> Error sending to API: {e}")


def main():
    print("=" * 50)
    print("H.E.R.M.E.S. Serial Reader")
    print("Listening for Arduino sensor data...")
    print("=" * 50)

    ser = connect_serial()

    while True:
        try:
            # Read a line from the Arduino
            raw_line = ser.readline().decode("utf-8").strip()

            # Skip empty lines
            if not raw_line:
                continue

            print(f"\nRaw data: {raw_line}")

            # Parse the JSON from Arduino
            data = json.loads(raw_line)

            # Check if it's an error message from the Arduino
            if "error" in data:
                print(f"  Sensor error: {data['error']}")
                continue

            # Map Arduino field names to what the API expects
            payload = {
                "co2": data.get("co2", 0),
                "co": data.get("co_mq2", 0),
                "air": data.get("mq135_raw", 0),
                "temperature": data.get("temp_f", 0.0),
                "humidity": data.get("humidity", 0.0),
                "aq_percent": data.get("aq_percent", 0),
                "alert": data.get("alert", False)
            }

            print(f"  Parsed: Temp={payload['temperature']}F, "
                  f"CO2={payload['co2']}ppm, "
                  f"AQ={payload['aq_percent']}%")

            send_to_api(payload)

        except json.JSONDecodeError:
            # Sometimes we get partial lines, just skip them
            print(f"  Bad JSON, skipping: {raw_line[:50]}")

        except serial.SerialException:
            print("Lost connection to Arduino, reconnecting...")
            ser.close()
            time.sleep(2)
            ser = connect_serial()

        except KeyboardInterrupt:
            print("\nShutting down serial reader.")
            ser.close()
            sys.exit(0)

        except Exception as e:
            print(f"  Unexpected error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
