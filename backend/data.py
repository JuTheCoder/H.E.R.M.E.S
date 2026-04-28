"""
data.py: handles the assignment of safety ratings for
each sensor reading based on returned values, also
assigns a safety rating to the overall quality by
summing up the ratings of the individual readings.
"""

# This will hold the custom theshold values that the user wants
custom_thresholds = {}
print("Custom threshold: ", custom_thresholds)

def threshold(name, value):
    """
    Determines the safety level of each sensor reading by assigning it
    a safety level depending on the range of its returned numerical value;.
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
        print("Settings: ", settings)

        if settings["safe_min"] <= value <= settings["safe_max"]:
            return "Safe"
        if(settings["moderate_low_min"] <= value <= settings["moderate_low_max"] or
           settings["moderate_high_min"] <= value <= settings["moderate_high_max"]):
            return "Moderate"

        return "Unsafe"

    if name == "co2" :
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
        if 101 <= value <= 150:
            return "Unhealthy for sensitive groups"
        if 151 <= value <= 200:
            return "Unhealthy"
        if 201 <= value <= 300:
            return "Very Unhealthy"
        if value > 300:
            return "Hazardous"
        return "No Data"
    return "No Data"

def severity_score(label):
    """
    Maps each of the threshold labels to a number that we will 
    use to determine the overall environmental quality.
    """
    scores = {
        "No Data": -1,
        #"Good": 0,
        "Safe": 0,
        "Moderate": 1,
        "Poor": 2,
        #"Unhealthy for sensitive groups": 2,
        "Unsafe": 3,
        #"Unhealthy": 3,
        "Dangerous": 4,
        "Very Unhealthy": 4,
        "Hazardous": 4,
        "Severe Danger": 4
    }

    return scores.get(label,-1)

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

    if max_score == -1:
        return "No Data"
    if max_score == 0:
        return "Safe"
    if max_score == 1:
        return "Moderate"
    if max_score == 2:
        return "Poor"
    if max_score == 3:
        return "Unsafe"
    if max_score == 4:
        return "Dangerous"
    return "None"
