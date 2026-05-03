"""
data.py: handles the assignment of safety ratings for
each sensor reading based on returned values, also
assigns a safety rating to the overall quality by
summing up the ratings of the individual readings.
"""

# This will hold the custom theshold values that the user wants
custom_thresholds = {}

def threshold(name, value):
    """
    Determines the safety level of each sensor reading by assigning it
    a safety level depending on the range of its returned numerical value.
    """
    if value is None:
        return "No Data"

    if name == "temperature":
        settings = custom_thresholds.get("temperature", {
            "safe_min": 68,
            "safe_max": 77,
            "moderate_low_min": 60,
            "moderate_low_max": 67,
            "moderate_high_min": 78,
            "moderate_high_max": 85
        })

        if(settings["safe_min"] <= value <= settings["safe_max"]):
            return "Safe"
        elif(settings["moderate_low_min"] <= value <= settings["moderate_low_max"]) or (settings["moderate_high_min"] <= value <= settings["moderate_high_max"]):
            return "Moderate"
        else:
            return "Unsafe"

    if name == "co2":
        if 400 <= value <= 800:
            return "Safe"
        if 801 <= value <= 1000:
            return "Moderate"
        if 1001 <= value <= 2500:
            return "Unsafe"
        if 2501 <= value <= 5000:
            return "Poor"
        if value > 5000:
            return "Dangerous"
        return "No Data"
    if name == "co":
        if 0 <= value <= 14:
            return "Safe"
        if 15 <= value <= 34:
            return "Moderate"
        if 35 <= value <= 75:
            return "Unsafe"
        if 76 <= value <= 149:
            return "Dangerous"
        if value > 150:
            return "Severe Danger"
        return "No Data"
    if name == "air":
        if 0 <= value <= 150:
            return "Safe"
        if 151 <= value <= 400:
            return "Moderate"
        if 401 <= value <= 1000:
            return "Unsafe"
        if 1001 <= value <= 5000:
            return "Dangerous"
        if value > 5000:
            return "Severe Danger"
        return "No Data"
    return "No Data"

def severity_score(label):
    """
    Maps each of the threshold labels to a number that we will
    use to determine the overall environmental quality.
    """
    scores = {
        "No Data": -1,
        "Safe": 0,
        "Moderate": 1,
        "Poor": 2,
        "Unsafe": 3,
        "Dangerous": 4,
        "Very Unhealthy": 4,
        "Severe Danger": 5
    }

    return scores.get(label, -1)

def overall_threshold(temp, co2, co, air):
    """
    Defines the overall quality of air given the threshold of
    each air characteristic.
    """
    labels = [
        threshold("temperature", temp),
        threshold("co2", co2),
        threshold("co", co),
        threshold("air", air)
    ]

    max_score = -1

    for label in labels:
        score = severity_score(label)
        max_score = max(max_score, score)

    num_to_severity = {
        -1: "No Data",
        0: "Safe",
        1: "Moderate",
        2: "Poor",
        3: "Unsafe",
        4: "Dangerous",
        5: "Severe Danger"
    }
    return num_to_severity.get(max_score, "Severe Danger")
