"""
alert system for HERMES.
sends whatsapp messages when sensor readings go above safe.
uses Twilio WhatsApp sandbox - no toll-free verification needed.
"""

import json
import os
import time

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "alert_config.json")

# don't spam messages - wait at least 5 min between alerts
COOLDOWN = 300
last_alert_time = 0


def load_config():
    """pull the twilio creds and phone numbers from config file"""
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_default_config():
    """drop a blank config file so the user knows what to fill in"""
    config = {
        "twilio_sid": "YOUR_ACCOUNT_SID_HERE",
        "twilio_token": "YOUR_AUTH_TOKEN_HERE",
        "twilio_whatsapp": "whatsapp:+14155238886",
        "alert_phones": ["whatsapp:+1XXXXXXXXXX"],
        "enabled": False
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    print("Created alert_config.json - fill in your Twilio creds to enable WhatsApp alerts")


def is_configured():
    """check if twilio creds are actually filled in"""
    config = load_config()
    if not config:
        return False
    if not config.get("enabled", False):
        return False
    if "YOUR_" in config.get("twilio_sid", "YOUR_"):
        return False
    return True


def check_and_alert(sensor_data, thresholds):
    """
    look at the current thresholds and fire off a whatsapp message
    if anything is above safe. respects the cooldown so
    we don't blow up someone's phone.
    """
    global last_alert_time

    if not is_configured():
        return

    now = time.time()
    if now - last_alert_time < COOLDOWN:
        return

    # figure out what's actually bad right now
    bad_readings = []

    checks = {
        "Temperature": thresholds.get("temp_thresh", "Safe"),
        "CO2": thresholds.get("co2_thresh", "Safe"),
        "CO": thresholds.get("co_thresh", "Safe"),
        "Air Quality": thresholds.get("air_thresh", "Safe"),
    }

    safe_labels = ["Safe", "Good", "Comfortable", "Moderate", "No Data", "Unknown"]

    for name, status in checks.items():
        if status not in safe_labels:
            bad_readings.append(f"{name}: {status}")

    if not bad_readings:
        return

    # build the message
    msg = "HERMES ALERT\n"
    msg += "Unsafe conditions detected:\n"
    for reading in bad_readings:
        msg += f"- {reading}\n"
    msg += f"\nTemp: {sensor_data.get('temperature', 0)}F"
    msg += f"\nCO2: {sensor_data.get('co2', 0)}ppm"
    msg += f"\nCO raw: {sensor_data.get('co', 0)}"
    msg += f"\nAQ: {sensor_data.get('aq_percent', 0)}%"

    send_whatsapp(msg)
    last_alert_time = now


def send_whatsapp(message):
    """send the alert through twilio whatsapp"""
    config = load_config()
    if not config:
        return

    try:
        from twilio.rest import Client
        client = Client(config["twilio_sid"], config["twilio_token"])

        from_number = config.get("twilio_whatsapp", "whatsapp:+14155238886")

        for phone in config.get("alert_phones", []):
            # make sure the number has the whatsapp: prefix
            to_number = phone if phone.startswith("whatsapp:") else "whatsapp:" + phone

            client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            print(f"WhatsApp alert sent to {to_number}")

    except ImportError:
        print("twilio package not installed - run: pip3 install twilio")
    except Exception as e:
        print(f"Failed to send WhatsApp: {e}")
