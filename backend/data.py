"""
data.py: handles the assignment of safety ratings for
each sensor reading based on returned values, also
assigns a safety rating to the overall quality by
summing up the ratings of the individual readings.
"""
def threshold(name, value):
    """
    Determines the safety level of each sensor reading by assigning it
    a safety level depending on the range of its returned numerical value;.
    """
    if value is None:
        return "No Data"
    if name == "temperature":
        if 68 <= value <= 77:
            return "Safe"
        if (45 <= value <= 67) or (78 <= value <= 85):
            return "Moderate"
        if (value < 45) or (85 < value):
            return "Unsafe"
    if name == "co2":
        if 0 <= value <= 800:
            return "Safe"
        if 801 <= value <= 1000:
            return "Moderate"
        if 1001 <= value <= 2500:
            return "Unsafe"
        if 2501 <= value <= 5000:
            return "Poor"
        if value > 5000:
            return "Dangerous"
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
    return None
    # if name == "air":
    #     if 0 <= value <= 50:
    #         return "Good"
    #     if 51 <= value <= 100:
    #         return "Moderate"
    #     if 101 <= value <= 150:
    #         return "Unhealthy for sensitive groups"
    #     if 151 <= value <= 200:
    #         return "Unhealthy"
    #     if 201 <= value <= 300:
    #         return "Very Unhealthy"
    #     if value > 300:
    #         return "Hazardous"

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
        #"Very Unhealthy": 4,
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

    # Assigns a severity level based on the returned number
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
