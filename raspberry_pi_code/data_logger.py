"""
H.E.R.M.E.S. - Data Logger
Reads sensor data from Arduino over serial and makes it available
to the FastAPI backend (main.py).

REQUIRED: pip3 install pyserial

USAGE:
  python3 data_logger.py

FIND YOUR PORT (Mac):
  ls /dev/tty.usb*
  or ls /dev/cu.usb*
  Example: /dev/cu.usbmodem14101
"""

import serial
import json
import time
import os

# ---- Configuration ----
SERIAL_PORT = "/dev/cu.usbmodem14101"  # <-- CHANGE THIS to your Arduino's port
BAUD_RATE   = 9600                      # Must match sensors.ino
OUTPUT_FILE = "latest_readings.json"    # Shared file for data.py to read

def connect_serial(port, baud, retries=5):
    """Attempt to connect to the Arduino serial port."""
    for attempt in range(retries):
        try:
            ser = serial.Serial(port, baud, timeout=2)
            print(f"Connected to {port} at {baud} baud.")
            time.sleep(2)  # Wait for Arduino to reset after serial connection
            return ser
        except serial.SerialException as e:
            print(f"Attempt {attempt + 1}/{retries} - Could not connect: {e}")
            time.sleep(2)
    print("Failed to connect after all retries.")
    return None


def parse_line(line):
    """Parse a JSON line from the Arduino serial output."""
    try:
        data = json.loads(line.strip())
        return data
    except json.JSONDecodeError:
        # Skip non-JSON lines (e.g., startup messages like "Warm-up complete")
        return None


def save_readings(readings):
    """Save the latest readings to a JSON file for data.py to consume."""
    with open(OUTPUT_FILE, "w") as f:
        json.dump(readings, f, indent=2)


def main():
    print("H.E.R.M.E.S. Data Logger Starting...")
    print(f"Connecting to serial port: {SERIAL_PORT}")

    ser = connect_serial(SERIAL_PORT, BAUD_RATE)
    if ser is None:
        return

    print("Listening for sensor data... (Ctrl+C to stop)")
    print("---")

    try:
        while True:
            if ser.in_waiting > 0:
                raw_line = ser.readline().decode("utf-8", errors="replace")
                data = parse_line(raw_line)

                if data:
                    # Display in terminal
                    print(f"Temp: {data.get('temperature', '?')}°F  |  "
                          f"Humidity: {data.get('humidity', '?')}%  |  "
                          f"MQ135 Raw: {data.get('mq135_raw', '?')}  |  "
                          f"MQ135 Voltage: {data.get('mq135_voltage', '?')}V")

                    # Map to the format data.py and main.py expect
                    mapped = {
                        "temperature": data.get("temperature", 0),
                        "co2": data.get("mq135_raw", 0),        # MQ135 detects CO2
                        "co": 0,                                  # MQ2 handles CO (teammate's sensor)
                        "air_quality": data.get("mq135_raw", 0)  # MQ135 also does air quality
                    }
                    save_readings(mapped)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping data logger.")
    finally:
        ser.close()
        print("Serial connection closed.")


if __name__ == "__main__":
    main()
