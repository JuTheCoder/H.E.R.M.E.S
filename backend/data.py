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

    defaults = {
        "temperature": {"safe_min": 68, "safe_max": 77, "moderate_low_min": 60,
                        "moderate_low_max": 67, "moderate_high_min": 78, "moderate_high_max": 85},
        "co2": {"safe_min": 400, "safe_max": 800, "moderate_low_min": 300,
                "moderate_low_max": 399, "moderate_high_min": 801, "moderate_high_max": 1000},
        "co": {"safe_min": 0, "safe_max": 14, "moderate_low_min": 0,
               "moderate_low_max": 0, "moderate_high_min": 15, "moderate_high_max": 34},
        "air": {"safe_min": 0, "safe_max": 150, "moderate_low_min": 0,
                "moderate_low_max": 0, "moderate_high_min": 151, "moderate_high_max": 400}
    }

    # Get user settings OR use the defaults defined above
    settings = custom_thresholds.get(name, defaults.get(name))

    if settings is None:
        return "No Data"

    if settings["safe_min"] <= value <= settings["safe_max"]:
        return "Safe"
    if (settings["moderate_low_min"] <= value <= settings["moderate_low_max"] or
        settings["moderate_high_min"] <= value <= settings["moderate_high_max"]):
        return "Moderate"

    return "Unsafe"

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
