from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data import threshold, overall_threshold

# Stores latest reading
latest_data = {}

app = FastAPI()

# This list holds the html's source
origins = [
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# Format for threshold endpoint
class Threshold(BaseModel):
    temp_thresh: str
    co2_thresh: str
    co_thresh: str
    air_thresh: str
    overall_thresh: str

# Format for the data endpoint
class SensorReading(BaseModel):
    co2: int
    co: int
    air: int
    temperature: float

# Recieves data from the raspberry pi and stores each value into a variable in our global dictionary
@app.post("/api/sensor-data")
def receive_sensor_data(reading: SensorReading):
    global latest_data
    latest_data = {
        "temperature": reading.temperature,
        "co2": reading.co2,
        "co": reading.co,
        "air": reading.air
    }
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

# endpoint that'll display the threshold for each air level
@app.get("/api/threshold", response_model=Threshold)
def thold():
    temp_thresh = threshold("temperature", latest_data.get("temperature", 0.0)),
    co2_thresh = threshold("co2", latest_data.get("co2", 0)),
    co_thresh = threshold("co", latest_data.get("co", 0)),
    air_thresh = threshold("air", latest_data.get("air", 0)),

    overall_thresh = overall_threshold(temp_thresh, co2_thresh, co_thresh, air_thresh)

    return {
        "temperature_thresh": temp_thresh,
        "co2_thresh": co2_thresh,
        "co_thresh": co_thresh,
        "air_thresh": air_thresh,
        "overall_thresh": overall_thresh
    }


    
    
@app.get("/api/test")
def test():
    return{"message": "Good"}


