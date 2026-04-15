
# This function determines the threshold of each air characteristic by it's name and value
def threshold(name, value):
    if value is None: 
        return "No Data"
    if(name == "temperature"):
        if(value >= 68 and value <= 77):
            return "Safe"
        elif((value >= 60 and value <= 67) or (value >= 78 and value <= 85)):
            return "Moderate"
        elif(value < 60 or value > 85):
            return "Unsafe"
    if(name == "co2"):
        if(value >= 400 and value <= 800):
            return "Safe"
        elif(value >= 801 and value <= 1000):
            return "Moderate"
        elif(value >= 1001 and value <= 2000):
            return "Poor"
        elif(value >= 2001 and value <= 5000):
            return "Unsafe"
        elif(value > 5000):
            return "Dangerous"
    if(name == "co"):
        if(value >= 0 and value <= 5):
            return "Safe"
        elif(value >= 6 and value <= 9):
            return "Moderate"
        elif(value >= 10 and value <= 35):
            return "Unsafe"
        elif(value >= 36 and value <= 200):
            return "Dangerous"
        elif(value > 200):
            return "Severe Danger"
    if(name == "air"):
        if(value >= 0 and value <= 50):
            return "Good"
        elif(value >= 51 and value <= 100):
            return "Moderate"
        elif(value >= 101 and value <= 150):
            return "Unhealthy for sensitive groups"
        elif(value >= 151 and value <= 200):
            return "Unhealthy"
        elif(value >= 201 and value <= 300):
            return "Very Unhealthy"
        elif(value > 300):
            return "Hazardous"

# This function maps each of the threshold labels to a number that we will use to determine the overall quality
def severity_score(label):
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
    }

    return scores.get(label,-1)

# Defines the overall quality of air given the threshold of each air characteristic
def overall_threshold(temp, co2, co, air):
    labels = [
        threshold("temperature", temp), #
        threshold("co2", co2),
        threshold("co", co),
        threshold("air", air)
    ]

    max_score = -1

    for label in labels:
        score = severity_score(label)
        if score > max_score:
            max_score = score

    if max_score == -1:
        return "No Data"
    elif max_score == 0:
        return "Safe"
    elif max_score == 1:
        return "Moderate"
    elif max_score == 2:
        return "Poor"
    elif max_score == 3:
        return "Unsafe"
    elif max_score == 4:
        return "Dangerous"
    else: 
        return "Severe Danger"