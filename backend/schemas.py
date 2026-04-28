"""
schemas.py: Contains the Pydantic schemas 
for API data validation.
"""

from pydantic import BaseModel

class SensorReading(BaseModel):
    """
    Configuration for sensor readings.
    """
    co2: int
    co: int
    air: int
    temperature: float

class TempThresholds(BaseModel):
    """
    Configuration for user-defined temperature thresholds.
    """
    safe_min: int
    safe_max: int
    moderate_low_min: int
    moderate_low_max: int
    moderate_high_min: int
    moderate_high_max: int

class Threshold(BaseModel):
    """
    Configuration for sensor reading thresholds.
    """
    temp_thresh: str
    co2_thresh: str
    co_thresh: str
    air_thresh: str
    overall_thresh: str
