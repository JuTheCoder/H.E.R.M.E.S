from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data import threshold

# Global dictionary for all sensor values
#value_list = {
#   "temperature": 0,
#    "co2": 0,
#    "co": 0,
#    "air_quality": 0
#}

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

class Threshold(BaseModel):
    temp_thresh: str
    co2_thresh: str
    co_thresh: str
    air_thresh: str

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

@app.get("/api/threshold", response_model=Threshold)
def thold():
    return {
        "temp_thresh": threshold("temperature", latest_data.get("temperature", 0.0)),
        "co2_thresh": threshold("co2", latest_data.get("co2", 0)),
        "co_thresh": threshold("co", latest_data.get("co", 0)),
        "air_thresh": threshold("air", latest_data.get("air", 0))
    }
    
@app.get("/api/test")
def test():
    return{"message": "Good"}


