"""
main.py
"""
import time
import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data import threshold, overall_threshold

# Stores latest reading
latest_data = {
    "temperature": 0.0,
    "co2": 0,
    "co": 0,
    "air": 0
}

# Variables used to prevent alert spamming
last_alert_time = 0
COOLDOWN_SECONDS = 1800  # 30 Minutes

# Loads the env to utilize Twilio
load_dotenv()

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

app = FastAPI()

# Holds the html's source
origins = [
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Format for the threshold endpoint
class Threshold(BaseModel):
    """
    Configuration for sensor reading thresholds.
    """
    temp_thresh: str
    co2_thresh: str
    co_thresh: str
    air_thresh: str
    overall_thresh: str

# Format for the data endpoint
class SensorReading(BaseModel):
    """
    Configuration for sensor readings.
    """
    co2: int
    co: int
    air: int
    temperature: float

def send_twilio_sms(message_body: str):
    """
    Sends an SMS using the Twilio's API, also includes debugging 
    messages in the event of failure based on error codes.
    """
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"

    data = {
        "From": TWILIO_PHONE,
        "To": MY_PHONE,
        "Body": message_body
    }

    try:
        response = requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=10)

        if 200 <= response.status_code < 300:
            print("Twilio Alert Sent Successfully!")
            return True
        else:
            print(f"Twilio Alert Failed! Status: {response.status_code}")

            print(f"DEBUG INFO: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Network Error: {e}")
        return False

@app.post("/api/sensor-data")
async def receive_sensor_data(reading: SensorReading):
    """
    Receives and stores the readings being from the Arduino,
    checks if any levels are dangerous, and alerts the user
    if necessary.
    """
    global last_alert_time

    # Updates latest data for the UI
    latest_data["co2"] = reading.co2
    latest_data["co"] = reading.co
    latest_data["air"] = reading.air
    latest_data["temperature"] = reading.temperature

    # Checks if any of the returned values are higher than their threshold
    is_dangerous = reading.co2 > 10000

    current_time = time.time()

    if is_dangerous:
        # 3. Check Cooldown (Prevents SMS spam)
        if (current_time - last_alert_time) > COOLDOWN_SECONDS:
            alert_msg = f"""
                H.E.R.M.E.S. ALERT: Dangerous Levels Detected!\n 
                Current Readings: CO2: {reading.co2}ppm,\n CO: {reading.co}ppm,\n
                AQ: {reading.air},\n Temp: {reading.temperature}
                """

            success = send_twilio_sms(alert_msg)

            if success:
                last_alert_time = current_time
        else:
            # Helpful for debugging to see why texts aren't being received
            remaining = int(COOLDOWN_SECONDS - (current_time - last_alert_time))
            print(f"Alert suppressed: Cooldown active for {remaining // 60} more minutes.")

    return {"status": "data received"}

# endpoint that'll display the data for each sensor reading
@app.get("/api/data", response_model=SensorReading)
def retrieve_data():
    """
    Retrieves latest data for all four sensor readings.
    """
    print(latest_data)
    return {
        "temperature": latest_data.get("temperature", 0.0),
        "co2": latest_data.get("co2", 0),
        "co": latest_data.get("co", 0),
        "air": latest_data.get("air", 0)
    }

@app.get("/api/threshold", response_model=Threshold)
def thold():
    """
    Retrieves all threshold values that have been determined based on
    readings, and combines them into an overall threshold value to be
    displayed on the UI.
    """
    temp_thresh = threshold("temperature", latest_data.get("temperature", 0.0))
    co2_thresh = threshold("co2", latest_data.get("co2", 0))
    co_thresh = threshold("co", latest_data.get("co", 0))
    air_thresh = threshold("air", latest_data.get("air", 0))
    overall_thresh = overall_threshold(latest_data.get("temperature", 0.0),
                                       latest_data.get("co2", 0),
                                       latest_data.get("co", 0),
                                       latest_data.get("air", 0))

    return {
        "temp_thresh": temp_thresh,
        "co2_thresh": co2_thresh,
        "co_thresh": co_thresh,
        "air_thresh": air_thresh,
        "overall_thresh": overall_thresh
    }
