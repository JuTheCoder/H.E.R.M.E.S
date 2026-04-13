import time
import requests
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data import threshold
from dotenv import load_dotenv

# Load the variables from the .env file
load_dotenv()

# Stores latest reading
latest_data = {
    "temperature": 0.0,
    "co2": 0,
    "co": 0,
    "air": 0
}

# State tracking for alerts to prevent spamming
last_alert_time = 0
COOLDOWN_SECONDS = 1800  # 30 Minutes

# Twilio Configuration - Replace these with your actual Twilio Console values
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

app = FastAPI()

# This list holds the html's source
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

# Format for threshold endpoint
class Threshold(BaseModel):
    temp_thresh: str
    co2_thresh: str
    co_thresh: str
    air_thresh: str

# Format for the data endpoint
class SensorReading(BaseModel):
    co2: int
    co: int
    air: int
    temperature: float

def send_twilio_sms(message_body: str):
    """
    Sends an SMS using Twilio's REST API via the requests library.
    Returns True if successful, False otherwise.
    """
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    
    data = {
        "From": TWILIO_PHONE,
        "To": MY_PHONE,
        "Body": message_body
    }
    
    try:
        # Added 10s timeout to prevent hanging (Pylint W3101)
        response = requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=10)
        
        if 200 <= response.status_code < 300:
            print("✅ Twilio Alert Sent Successfully!")
            return True # Fixes Pylint E1111
        else:
            print(f"❌ Twilio Alert Failed! Status: {response.status_code}")
            # THIS LINE TELLS US EXACTLY WHY IT FAILED (e.g., Unverified Number)
            print(f"DEBUG INFO: {response.text}")
            return False # Fixes Pylint E1111
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False

@app.post("/api/sensor-data")
async def receive_sensor_data(reading: SensorReading):
    global last_alert_time

    # 1. Update the latest data for the dashboard
    latest_data["co2"] = reading.co2
    latest_data["co"] = reading.co
    latest_data["air"] = reading.air
    latest_data["temperature"] = reading.temperature

    # 2. Logic Gate: Check for Danger
    # Based on your H.E.R.M.E.S. thresholds
    is_dangerous = reading.co2 > 4000 or reading.co > 400

    current_time = time.time()

    if is_dangerous:
        # 3. Check Cooldown (Prevents SMS spam)
        if (current_time - last_alert_time) > COOLDOWN_SECONDS:
            alert_msg = f"⚠️ H.E.R.M.E.S. ALERT: Dangerous Levels! CO2: {reading.co2}ppm, CO: {reading.co}ppm"
            
            # Use the dedicated send function
            success = send_twilio_sms(alert_msg)
            
            if success:
                last_alert_time = current_time
        else:
            # Helpful for debugging to see why it isn't texting
            remaining = int(COOLDOWN_SECONDS - (current_time - last_alert_time))
            print(f"Alert suppressed: Cooldown active for {remaining // 60} more minutes.")

    return {"status": "data received"}

# endpoint that'll display the data for each air level
@app.get("/api/data", response_model=SensorReading)
def data():
    print(latest_data)
    return {
        "temperature": latest_data.get("temperature", 0.0),
        "co2": latest_data.get("co2", 0),
        "co": latest_data.get("co", 0),
        "air": latest_data.get("air", 0)
    }

@app.get("/api/threshold", response_model=Threshold)
def thold():
    # Use .get() with defaults and wrap in str() to satisfy the Pydantic model
    return {
        "temp_thresh": str(threshold("temperature", latest_data.get("temperature", 0.0)) or "Safe"),
        "co2_thresh": str(threshold("co2", latest_data.get("co2", 4000)) or "Safe"),
        "co_thresh": str(threshold("co", latest_data.get("co", 0)) or "Safe"),
        "air_thresh": str(threshold("air", latest_data.get("air", 0)) or "Safe")
    }
    
@app.get("/api/test")
def test():
    return {"message": "Good"}

@app.get("/api/test-sms")
def test_sms():
    # This manually calls your existing send_sms function
    success = send_twilio_sms("H.E.R.M.E.S. Test: The Twilio integration is working!")
    if success:
        return {"status": "Success", "message": "Check your phone!"}
    else:
        # Check your terminal if this fails; it will print the error
        return {"status": "Error", "message": "Failed to send. Check terminal."}
