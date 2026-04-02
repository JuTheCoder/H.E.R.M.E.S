
#def values():
    #levels = {
        #"temperature": 0,
       # "co2": 0,
       # "co": 0,
       # "air_quality": 0
   # }
   #return levels

def threshold(name, value):
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
    if(name == "air_quality"):
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