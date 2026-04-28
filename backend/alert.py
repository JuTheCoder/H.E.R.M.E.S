"""
alert.py: Handles remote alerts through Twilio. It's 
utilized by main.py if dangerous levels are detected,
so a remote alert can be sent by users. Uses env variables
to determine where alert source and destination.
"""

import time
import os
import requests
from dotenv import load_dotenv
from schemas import SensorReading

# Loads the env to utilize Twilio
load_dotenv()

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

# Variables used to prevent alert spamming
LAST_ALERT_TIME = 0
COOLDOWN_SECONDS = 1800  # 30 Minutes

def send_twilio_alert(message_body: str):
    """
    Sends an alert using Twilio's API, also includes debugging 
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

def handle_alert(is_dangerous: bool, reading: SensorReading):
    """
    Handles the entire alert process: cooldown check,
    message creation, and sending. Returns: 
    (bool: True if sent, False if suppressed or not needed)
    """
    global LAST_ALERT_TIME

    if not is_dangerous:
        return False

    current_time = time.time()

    # Check Cooldown
    if (current_time - LAST_ALERT_TIME) > COOLDOWN_SECONDS:
        alert_msg = f"""
            H.E.R.M.E.S. ALERT: Dangerous Levels Detected!\n 
            Current Readings: CO2: {reading.co2}ppm,\n CO: {reading.co}ppm,\n
            AQ: {reading.air},\n Temp: {reading.temperature}
            """

        success = send_twilio_alert(alert_msg)

        if success:
            LAST_ALERT_TIME = current_time
            return True
        return False

    remaining = int(COOLDOWN_SECONDS - (current_time - LAST_ALERT_TIME))
    print(f"Alert suppressed: Cooldown active for {remaining // 60} more minutes.")
    return False
