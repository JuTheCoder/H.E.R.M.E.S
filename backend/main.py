"""
HERMES Backend API
Handles sensor data, serves the dashboard, manages auth, and triggers alerts.
Run with: python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
For HTTPS: python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=certs/key.pem --ssl-certfile=certs/cert.pem
"""

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from data import threshold, overall_threshold, severity_score, get_thresholds_config, save_thresholds
from auth import authenticate, verify_token, setup_default_accounts, create_user, list_users, delete_user
from alerts import check_and_alert, save_default_config, is_configured
import json
import os

app = FastAPI(title="H.E.R.M.E.S. API")

# CORS - locked down to just our own origin
origins = [
    "https://127.0.0.1:8000",
    "https://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# make sure we have default accounts on first boot
setup_default_accounts()

# drop a blank alert config if there isn't one
if not os.path.exists(os.path.join(os.path.dirname(__file__), "alert_config.json")):
    save_default_config()


# --- models that match what the arduino sends ---

class SensorReading(BaseModel):
    co2: int = 0
    co: int = 0
    air: int = 0
    temperature: float = 0.0
    humidity: Optional[float] = 0.0
    aq_percent: Optional[int] = 0
    alert: Optional[bool] = False

class LoginRequest(BaseModel):
    username: str
    password: str

class NewUserRequest(BaseModel):
    username: str
    password: str
    role: str = "viewer"


# --- in-memory storage ---

latest_data = {
    "temperature": 0.0,
    "co2": 0,
    "co": 0,
    "air": 0,
    "humidity": 0.0,
    "aq_percent": 0,
    "alert": False,
    "location": "unknown",
    "timestamp": ""
}

reading_history = []
MAX_HISTORY = 500

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "sensor_log.csv")


def save_to_csv(entry):
    """append reading to csv so we don't lose data on restart"""
    os.makedirs(LOG_DIR, exist_ok=True)
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a") as f:
        if not file_exists:
            f.write("timestamp,temperature,co2,co,air,humidity,aq_percent,alert,location\n")
        f.write(
            f"{entry['timestamp']},"
            f"{entry['temperature']},"
            f"{entry['co2']},"
            f"{entry['co']},"
            f"{entry['air']},"
            f"{entry['humidity']},"
            f"{entry['aq_percent']},"
            f"{entry['alert']},"
            f"{entry['location']}\n"
        )


# --- auth helpers ---

# these paths skip auth - login page, login endpoint, sensor POST
NO_AUTH_PATHS = ["/api/login", "/api/sensor-data", "/login", "/login.html",
                 "/css/", "/js/", "/api/test", "/admin.html",
                 "/api/robot/", "/api/location"]


def check_auth(request: Request):
    """pull the token from cookies or auth header and validate it"""
    # skip auth for login-related paths and sensor data endpoint
    path = request.url.path
    for skip in NO_AUTH_PATHS:
        if path.startswith(skip):
            return None

    # check cookie first, then authorization header
    token = request.cookies.get("hermes_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        return None

    return verify_token(token)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """gate everything behind login except the paths we explicitly skip"""
    path = request.url.path

    # let these through no matter what
    for skip in NO_AUTH_PATHS:
        if path.startswith(skip):
            response = await call_next(request)
            return response

    # check for valid token
    token = request.cookies.get("hermes_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token or not verify_token(token):
        # if its a page request, redirect to login
        # if its an API call, return 401
        if path.startswith("/api/"):
            return JSONResponse(status_code=401, content={"detail": "not authenticated"})
        return RedirectResponse(url="/login.html")

    response = await call_next(request)
    return response


# --- auth endpoints ---

@app.post("/api/login")
def login(creds: LoginRequest, response: Response):
    """validate username/password and hand back a token cookie"""
    token = authenticate(creds.username, creds.password)
    if not token:
        raise HTTPException(status_code=401, detail="wrong username or password")

    response = JSONResponse(content={"status": "logged in", "token": token})
    response.set_cookie(
        key="hermes_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="strict"
    )
    return response


@app.post("/api/logout")
def logout(response: Response):
    """clear the auth cookie"""
    response = JSONResponse(content={"status": "logged out"})
    response.delete_cookie("hermes_token")
    return response


@app.post("/api/users")
def add_user(req: NewUserRequest, request: Request):
    """admin-only endpoint to create new accounts"""
    user = check_auth(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin only")

    from auth import create_user
    success, msg = create_user(req.username, req.password, req.role)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": msg}


@app.post("/api/change-password")
def change_password(request: Request, data: dict):
    """let a logged-in user change their own password"""
    user = check_auth(request)
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")

    from auth import load_users, save_users, hash_password, verify_password
    users = load_users()
    username = user["user"]
    if username not in users:
        raise HTTPException(status_code=404, detail="user not found")

    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "")

    if not verify_password(old_pw, users[username]["password"]):
        raise HTTPException(status_code=401, detail="current password is wrong")

    users[username]["password"] = hash_password(new_pw)
    save_users(users)
    return {"status": "password changed"}


# --- sensor data endpoints ---

@app.post("/api/sensor-data")
def receive_sensor_data(reading: SensorReading):
    """serial reader hits this every time it gets a new reading from the arduino"""
    global latest_data

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    latest_data = {
        "temperature": reading.temperature,
        "co2": reading.co2,
        "co": reading.co,
        "air": reading.air,
        "humidity": reading.humidity or 0.0,
        "aq_percent": reading.aq_percent or 0,
        "alert": reading.alert or False,
        "location": latest_data.get("location", "unknown"),
        "timestamp": now
    }

    history_entry = {**latest_data}
    reading_history.append(history_entry)

    if len(reading_history) > MAX_HISTORY:
        reading_history.pop(0)

    save_to_csv(history_entry)

    # check if we need to fire off a text alert
    thresholds = {
        "temp_thresh": threshold("temperature", reading.temperature),
        "co2_thresh": threshold("co2", reading.co2),
        "co_thresh": threshold("co", reading.co),
        "air_thresh": threshold("air_quality", reading.aq_percent or 0),
    }
    check_and_alert(latest_data, thresholds)

    print(f"[{now}] Temp: {reading.temperature}F, CO2: {reading.co2}ppm")
    return {"status": "received", "timestamp": now}


@app.get("/api/data")
def get_data():
    """latest readings for the dashboard"""
    return {
        "temperature": latest_data.get("temperature", 0.0),
        "co2": latest_data.get("co2", 0),
        "co": latest_data.get("co", 0),
        "air": latest_data.get("air", 0),
        "humidity": latest_data.get("humidity", 0.0),
        "aq_percent": latest_data.get("aq_percent", 0),
        "alert": latest_data.get("alert", False),
        "location": latest_data.get("location", "unknown"),
        "timestamp": latest_data.get("timestamp", "")
    }


@app.get("/api/threshold")
def get_thresholds():
    """safety levels for each sensor plus overall score"""
    temp_val = latest_data.get("temperature", 0.0)
    co2_val = latest_data.get("co2", 0)
    co_val = latest_data.get("co", 0)
    aq_val = latest_data.get("aq_percent", 0)

    overall = overall_threshold(temp_val, co2_val, co_val, aq_val)

    return {
        "temp_thresh": threshold("temperature", temp_val),
        "co2_thresh": threshold("co2", co2_val),
        "co_thresh": threshold("co", co_val),
        "air_thresh": threshold("air_quality", aq_val),
        "humidity_thresh": threshold("humidity", latest_data.get("humidity", 0.0)),
        "overall_thresh": overall
    }


@app.get("/api/history")
def get_history(limit: int = 50):
    """last N readings for the chart and table"""
    return reading_history[-limit:]


@app.post("/api/location")
def update_location(data: dict):
    """robot patrol script updates this with current zone"""
    global latest_data
    latest_data["location"] = data.get("location", "unknown")
    return {"status": "location updated", "location": latest_data["location"]}


@app.get("/api/status")
def system_status():
    """quick health check"""
    has_data = latest_data.get("timestamp", "") != ""
    return {
        "status": "online",
        "has_sensor_data": has_data,
        "last_reading": latest_data.get("timestamp", "no data yet"),
        "total_readings": len(reading_history),
        "sms_alerts": is_configured()
    }


@app.get("/api/alert-config")
def get_alert_config(request: Request):
    """check if SMS alerts are set up (admin only)"""
    user = check_auth(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return {"configured": is_configured()}


# --- admin endpoints ---

@app.get("/api/admin/thresholds")
def admin_get_thresholds(request: Request):
    """get current threshold config so the admin panel can display it"""
    user = check_auth(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return get_thresholds_config()


@app.post("/api/admin/thresholds")
def admin_set_thresholds(request: Request, data: dict):
    """save new threshold values from the admin panel"""
    user = check_auth(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    save_thresholds(data)
    return {"status": "thresholds updated"}


@app.get("/api/admin/users")
def admin_list_users(request: Request):
    """list all user accounts"""
    user = check_auth(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return list_users()


@app.delete("/api/admin/users/{username}")
def admin_delete_user(username: str, request: Request):
    """remove a user account"""
    user = check_auth(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    success, msg = delete_user(username)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": msg}


@app.get("/api/me")
def get_current_user(request: Request):
    """return who's currently logged in and their role"""
    user = check_auth(request)
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")
    return {"username": user["user"], "role": user["role"]}


# --- robot status ---

robot_status = {
    "blocked": False,
    "location": "idle",
    "running": False
}


@app.post("/api/robot/obstacle")
def robot_obstacle(data: dict):
    """patrol script reports an obstacle or clears it"""
    global robot_status
    robot_status["blocked"] = data.get("blocked", False)
    robot_status["location"] = data.get("location", "unknown")
    return {"status": "updated"}


@app.get("/api/robot/status")
def robot_get_status():
    """patrol script polls this to see if user cleared the obstacle"""
    return robot_status


@app.post("/api/robot/clear")
def robot_clear(request: Request):
    """user hits this from the dashboard to confirm path is clear"""
    global robot_status
    robot_status["blocked"] = False
    return {"status": "cleared"}


@app.get("/api/test")
def test():
    return {"message": "H.E.R.M.E.S. API is running"}


# serve the frontend from the same port
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
