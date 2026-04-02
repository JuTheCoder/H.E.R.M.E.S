from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data import threshold

# Global dictionary for all sensor values
value_list = {
    "temperature": 0,
    "co2": 0,
    "co": 0,
    "air_quality": 0
}

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

# Defining the json structure for our /data endpoint
class Sensor(BaseModel):
    temperature: float
    co2: float
    co: float
    air_quality: float

class Threshold(BaseModel):
    temp_thresh: str
    co2_thresh: str
    co_thresh: str
    air_thresh: str

class SensorReading(BaseModel):
    temperature: float
    co2: float
    co: float
    air_quality: float

# Recieves data from the raspberry pi and stores each value into a variable in our global dictionary
@app.post("/api/sensor-data")
def receive_sensor_data(reading: SensorReading):
    print("Temperature: ", reading.temperature)
    value_list["temperature"] = reading.temperature
    print("CO2: ", reading.co2)
    value_list["co2"] = reading.co2
    print("CO: ", reading.co)
    value_list["co"] = reading.co
    print("Air Quality: ", reading.air_quality)
    value_list["air_quality"] = reading.air_quality

    return {"status": "data received"}

# endpoint that'll display the data for each air level
@app.get("/api/data", response_model=Sensor)
def data():
    print(value_list)
    return {
        "temperature": value_list["temperature"],
        "co2": value_list["co2"],
        "co": value_list["co"],
        "air_quality": value_list["air_quality"]
    }

@app.get("/api/threshold", response_model=Threshold)
def thold():
    print("Before threshold:", value_list)
    temp_result = threshold("temperature", value_list["temperature"])
    co2_result = threshold("co2", value_list["co2"])
    co_result = threshold("co", value_list["co"])
    air_result = threshold("air_quality", value_list["air_quality"])
    print("After threshold:", value_list)
    return {
        "temp_thresh": temp_result,
        "co2_thresh": co2_result,
        "co_thresh": co_result,
        "air_thresh": air_result
    }
    
@app.get("/api/test")
def test():
    return{"message": "Good"}


