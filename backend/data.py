"""
Threshold logic for the sensors.
Admins can tweak these from the dashboard - changes save to thresholds.json.
Falls back to defaults based on OSHA/ASHRAE/EPA/WHO standards if no custom config.
"""

import json
import os

THRESHOLDS_FILE = os.path.join(os.path.dirname(__file__), "thresholds.json")

# these are the defaults if nobody has changed anything
DEFAULT_THRESHOLDS = {
    "temperature": {
        "safe_min": 68,
        "safe_max": 77,
        "moderate_min": 60,
        "moderate_max": 85,
        "unit": "F"
    },
    "co2": {
        "safe_max": 800,
        "moderate_max": 1000,
        "poor_max": 2000,
        "unsafe_max": 5000,
        "unit": "ppm"
    },
    "co": {
        "safe_max": 400,
        "moderate_max": 550,
        "unsafe_max": 700,
        "dangerous_max": 850,
        "unit": "raw"
    },
    "air_quality": {
        "good_max": 50,
        "moderate_max": 100,
        "sensitive_max": 150,
        "unhealthy_max": 200,
        "very_unhealthy_max": 300,
        "unit": "%"
    },
    "humidity": {
        "comfortable_min": 30,
        "comfortable_max": 50,
        "moderate_min": 20,
        "moderate_max": 60,
        "unit": "%"
    }
}


def load_thresholds():
    """grab custom thresholds from disk, or use defaults"""
    if os.path.exists(THRESHOLDS_FILE):
        with open(THRESHOLDS_FILE, "r") as f:
            custom = json.load(f)
            # merge with defaults so new fields don't break anything
            merged = {**DEFAULT_THRESHOLDS}
            for key in custom:
                if key in merged:
                    merged[key] = {**merged[key], **custom[key]}
            return merged
    return DEFAULT_THRESHOLDS.copy()


def save_thresholds(new_thresholds):
    """save custom threshold values to disk"""
    with open(THRESHOLDS_FILE, "w") as f:
        json.dump(new_thresholds, f, indent=2)


def get_thresholds_config():
    """return current thresholds for the admin panel"""
    return load_thresholds()


def threshold(name, value):
    """takes a sensor name and reading, returns a plain english risk level"""
    if value is None:
        return "No Data"

    t = load_thresholds()

    if name == "temperature":
        c = t["temperature"]
        if c["safe_min"] <= value <= c["safe_max"]:
            return "Safe"
        elif (c["moderate_min"] <= value < c["safe_min"]) or (c["safe_max"] < value <= c["moderate_max"]):
            return "Moderate"
        elif value < c["moderate_min"] or value > c["moderate_max"]:
            return "Unsafe"

    elif name == "co2":
        c = t["co2"]
        if value <= c["safe_max"]:
            return "Safe"
        elif value <= c["moderate_max"]:
            return "Moderate"
        elif value <= c["poor_max"]:
            return "Poor"
        elif value <= c["unsafe_max"]:
            return "Unsafe"
        elif value > c["unsafe_max"]:
            return "Dangerous"

    elif name == "co":
        c = t["co"]
        if value <= c["safe_max"]:
            return "Safe"
        elif value <= c["moderate_max"]:
            return "Moderate"
        elif value <= c["unsafe_max"]:
            return "Unsafe"
        elif value <= c["dangerous_max"]:
            return "Dangerous"
        elif value > c["dangerous_max"]:
            return "Severe Danger"

    elif name == "air_quality":
        c = t["air_quality"]
        if value <= c["good_max"]:
            return "Good"
        elif value <= c["moderate_max"]:
            return "Moderate"
        elif value <= c["sensitive_max"]:
            return "Unhealthy for Sensitive Groups"
        elif value <= c["unhealthy_max"]:
            return "Unhealthy"
        elif value <= c["very_unhealthy_max"]:
            return "Very Unhealthy"
        elif value > c["very_unhealthy_max"]:
            return "Hazardous"

    elif name == "humidity":
        c = t["humidity"]
        if c["comfortable_min"] <= value <= c["comfortable_max"]:
            return "Comfortable"
        elif (c["moderate_min"] <= value < c["comfortable_min"]) or (c["comfortable_max"] < value <= c["moderate_max"]):
            return "Moderate"
        elif value < c["moderate_min"] or value > c["moderate_max"]:
            return "Uncomfortable"

    return "Unknown"


def severity_score(label):
    """turn a threshold label into a number for comparison. higher = worse."""
    scores = {
        "No Data": -1,
        "Good": 0,
        "Safe": 0,
        "Comfortable": 0,
        "Moderate": 1,
        "Poor": 2,
        "Unhealthy for Sensitive Groups": 2,
        "Uncomfortable": 2,
        "Unsafe": 3,
        "Unhealthy": 3,
        "Dangerous": 4,
        "Very Unhealthy": 4,
        "Hazardous": 5,
        "Severe Danger": 5,
        "Unknown": -1
    }
    return scores.get(label, -1)


def overall_threshold(temp, co2, co, air):
    """worst of all four sensors becomes the overall verdict"""
    labels = [
        threshold("temperature", temp),
        threshold("co2", co2),
        threshold("co", co),
        threshold("air_quality", air)
    ]

    worst = -1
    for label in labels:
        score = severity_score(label)
        if score > worst:
            worst = score

    verdicts = {
        -1: "No Data",
        0: "Safe",
        1: "Moderate",
        2: "Poor",
        3: "Unsafe",
        4: "Dangerous",
        5: "Severe Danger"
    }
    return verdicts.get(worst, "No Data")
