"""
main.py: Handles the structure for endpoints and sensor readings,
continuously retrieves/stores sensor readings, and sends remote
alerts if any of the four thresholds are exceeded.
"""
import time
import os
import requests
import serial
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data import threshold, overall_threshold
#Lets FastAPI serve our frontend files directly instead of needing Live Server
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import FileResponse

#Authentication imports for login and protected endpoints 
from fastapi.security import OAuth2PasswordRequestForm
from auth import create_access_token, verify_password, get_current_user, USERS

# Stores latest reading
latest_data = {
    "temperature": 0.0,
    "co2": 0,
    "co": 0,
    "air": 0
}

# Variables used to prevent alert spamming
LAST_ALERT_TIME = 0
COOLDOWN_SECONDS = 1800  # 30 Minutes

# Loads the env to utilize Twilio
load_dotenv()

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

#Serial port for the Pi (change to /dev/cu.usbmodem101 for Mac testing)
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)

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
        print(f"Twilio Alert Failed! Status: {response.status_code}")

        print(f"DEBUG INFO: {response.text}")
        return False

    except requests.exceptions.RequestException as e:
        print(f"Network Error: {e}")
        return False
@app.post("/api/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates the user and returns a JWT token
    if the credentials are valid
    """
    user = USERS.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail= "Incorrect username or password")
    
    token = create_access_token(data={"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}



@app.post("/api/sensor-data")
async def receive_sensor_data(reading: SensorReading):
    """
    Receives and stores the readings being from the Arduino,
    checks if any levels are dangerous, and alerts the user
    if necessary.
    """
    global LAST_ALERT_TIME

    # Updates latest data for the UI
    latest_data["co2"] = reading.co2
    latest_data["co"] = reading.co
    latest_data["air"] = reading.air
    latest_data["temperature"] = reading.temperature

    # Checks if any of the returned values are higher than their threshold
    is_dangerous = reading.co2 > 1000

    # Sends communication back to Arduino based on alert status
    if ser.is_open:
        if is_dangerous:
            # Prompts system to beep and flash a red light
            ser.write(b'1')
        else:
            # Nothing happens/beeping and flashing turn off
            ser.write(b'0')

    current_time = time.time()

    if is_dangerous:
        # Check Cooldowns to prevent alert message spam
        if (current_time - LAST_ALERT_TIME) > COOLDOWN_SECONDS:
            alert_msg = f"""
                H.E.R.M.E.S. ALERT: Dangerous Levels Detected!\n 
                Current Readings: CO2: {reading.co2}ppm,\n CO: {reading.co}ppm,\n
                AQ: {reading.air},\n Temp: {reading.temperature}
                """

            success = send_twilio_sms(alert_msg)

            if success:
                LAST_ALERT_TIME = current_time
        else:
            # Helpful for debugging to see why texts aren't being received
            remaining = int(COOLDOWN_SECONDS - (current_time - LAST_ALERT_TIME))
            print(f"Alert suppressed: Cooldown active for {remaining // 60} more minutes.")

    return {"status": "data received"}

# Endpoint that'll display the data for each sensor reading
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

#Serves the frontend files (HTML, CSS, JS) straight from FastAPI
app.mount("/", StaticFiles(directory="../frontend", html=True), name ="frontend")


