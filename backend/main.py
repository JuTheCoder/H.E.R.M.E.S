from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from data import threshold, values

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
    air: float

class Threshold(BaseModel):
    temp_thresh: str
    co2_thresh: str
    co_thresh: str
    air_thresh: str

# endpoint that'll display the data for each air level
@app.get("/api/data", response_model=Sensor)
def data():
    value_list = values()
    return {
        "temperature": value_list["temperature"],
        "co2": value_list["co2"],
        "co": value_list["co"],
        "air": value_list["air_quality"]
    }

@app.get("/api/threshold", response_model=Threshold)
def thold():
    value_list = values()
    temp_result = threshold("temperature", value_list["temperature"])
    co2_result = threshold("co2", value_list["co2"])
    co_result = threshold("co", value_list["co"])
    air_result = threshold("air_quality", value_list["air_quality"])

    return {
        "temp_thresh": temp_result,
        "co2_thresh": co2_result,
        "co_thresh": co_result,
        "air_thresh": air_result
    }
    


