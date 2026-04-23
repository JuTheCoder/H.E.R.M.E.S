"""
data.py
"""

# This will hold the custom theshold values that the user wants
custom_thresholds = {}

def threshold(name, value):
    """
    Determines the threshold of each sensor reading by it's name and value
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
        """if 68 <= value <= 77:
            return "Safe"
        if (60 <= value <= 67) or (78 <= value <= 85):
            return "Moderate"
        if 60 < value > 85:
            return "Unsafe"""
        
    if name == "co2" :
        if 400 <= value <= 800:
            return "Safe"
        if 801 <= value <= 1000:
            return "Moderate"
        if 1001 <= value <= 2000:
            return "Poor"
        if 2001 <= value <= 5000:
            return "Unsafe"
        if value > 5000:
            return "Dangerous"
        return "No Data"
    if name == "co":
        if 0 <= value <= 5:
            return "Safe"
        if 6 <= value <= 9:
            return "Moderate"
        if 10 <= value <= 35:
            return "Unsafe"
        if 36 <= value <= 200:
            return "Dangerous"
        if value > 200:
            return "Severe Danger"
        return "No Data"
    if name == "air":
        if 0 <= value <= 50:
            return "Good"
        if 51 <= value <= 100:
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

        "Good": 0,
        "Safe": 0,

        "Moderate": 1,

        "Poor": 2,
        "Unhealthy for sensitive groups": 2,

        "Unsafe": 3,
        "Unhealthy": 3,

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
        # if score > max_score:
        #     max_score = score
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
