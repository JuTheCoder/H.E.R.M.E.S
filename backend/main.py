"""
main.py: Configures the FastAPI server, initializes 
serial hardware communication,and orchestrates API 
endpoints for real-time sensor data ingestion and 
threshold management.
"""
import time
import serial
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import data
from data import threshold, overall_threshold
from alert import handle_alert
from schemas import SensorReading, Threshold, TempThresholds, CO2Thresholds, COThresholds, AirThresholds

# Stores latest reading
latest_data = {
    "temperature": 0.0,
    "co2": 0,
    "co": 0,
    "air": 0
}

ser = serial.Serial('/dev/cu.usbmodem101', 9600, timeout=1)
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

@app.post("/api/sensor-data")
async def receive_sensor_data(reading: SensorReading):
    """
    Receives and stores the readings being from the Arduino,
    checks if any levels are dangerous, and alerts the user
    if necessary.
    """

    # Updates latest data for the UI
    latest_data["co2"] = reading.co2
    latest_data["co"] = reading.co
    latest_data["air"] = reading.air
    latest_data["temperature"] = reading.temperature

    # Checks if any of the returned values are higher than their threshold
    is_dangerous = reading.co2 > 10000

    # Sends communication back to Arduino based on alert status
    if ser.is_open:
        ser.write(b'1' if is_dangerous else b'0')

    handle_alert(is_dangerous, reading)

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

# POST endpoint that will allow the frontend to send the custom thresholds to our backend
@app.post("/api/temperature-threshold")
def set_temperature_threshold(data_in: TempThresholds):
    data.custom_thresholds["temperature"] = data_in.model_dump()
    return {"message": "Temperature thresholds updated",}

# POST endpoint that will reset the Temperature thresholds to its default settings/values
@app.post("/api/reset-temperature-threshold")
def reset_temperature_threshold():
    if "temperature" in data.custom_thresholds:
        del data.custom_thresholds["temperature"]

    return {"message": "Temperature thresholds reset to default"}

@app.post("/api/co2-threshold")
def set_co2_threshold(data_in: CO2Thresholds):
    data.custom_thresholds["co2"] = data_in.model_dump()
    return {"message": "CO2 thresholds updated",}

@app.post("/api/reset-co2-threshold")
def reset_co2_threshold():
    if "co2" in data.custom_thresholds:
        del data.custom_thresholds["co2"]

    return {"message": "CO2 thresholds reset to default"}

@app.post("/api/co-threshold")
def set_co_threshold(data_in: COThresholds):
    data.custom_thresholds["co"] = data_in.model_dump()
    return {"message": "CO thresholds updated",}

@app.post("/api/reset-co-threshold")
def reset_co_threshold():
    if "co" in data.custom_thresholds:
        del data.custom_thresholds["co"]

    return {"message": "CO thresholds reset to default"}

@app.post("/api/air-threshold")
def set_air_threshold(data_in: AirThresholds):
    data.custom_thresholds["air"] = data_in.model_dump()
    return {"message": "AQ thresholds updated",}

@app.post("/api/reset-air-threshold")
def reset_air_threshold():
    if "air" in data.custom_thresholds:
        del data.custom_thresholds["air"]

    return {"message": "AQ thresholds reset to default"}
