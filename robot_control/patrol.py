"""
HERMES Robot Patrol the Demo Route
Robot goes straight about 10 feet, turns around, comes back.
If something blocks the path, it stops, sends a WhatsApp alert,
and waits for the user to confirm the path is clear before continuing.

Uses the GoPiGo v1 board connected to the Pi over I2C
Usage: python3 patrol.py
Sim mode: python3 patrol.py --sim
"""

import time
import requests
import sys
import urllib3

#smbus is only available on the Pi for I2C communication
try:
    import smbus
except ImportError:
    smbus = None


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GoPiGo v1 I2C address
GOPIGO_ADDR = 0x08
bus = None

# API base URL for communicating with the HERMES backend
API_URL = "https://127.0.0.1:8000"

# How close something can be before we stop (centimeters)
OBSTACLE_THRESHOLD = 25

# How often to check for obstacles while moving (seconds)
CHECK_INTERVAL = 0.3

# Motor speed (0-255, we use 200 for a steady pace)
MOTOR_SPEED = 200

# I2C command bytes for GoPiGo v1 firmware
CMD_MOTOR1 = 111
CMD_MOTOR2 = 112
CMD_STOP = 120
CMD_ULTRASONIC = 117


def init_gopigo():
    """Set up the I2C connection to the GoPiGo board."""
    global bus
    try:
        bus = smbus.SMBus(1)
        print("Connected to GoPiGo over I2C")
        return True
    except Exception as e:
        print(f"Can't connect to GoPiGo: {e}")
        return False


def i2c_write(cmd, data):
    """Send an I2C command with retry on failure."""
    for attempt in range(3):
        try:
            bus.write_i2c_block_data(GOPIGO_ADDR, cmd, data)
            time.sleep(0.05)
            return True
        except IOError:
            time.sleep(0.1)
    return False


def motor_forward():
    """Both wheels forward."""
    i2c_write(CMD_MOTOR1, [0, MOTOR_SPEED, 0])
    i2c_write(CMD_MOTOR2, [0, MOTOR_SPEED, 0])


def motor_backward():
    """Both wheels backward."""
    i2c_write(CMD_MOTOR1, [1, MOTOR_SPEED, 0])
    i2c_write(CMD_MOTOR2, [1, MOTOR_SPEED, 0])


def motor_right():
    """Turn right - left wheel forward, right wheel backward."""
    i2c_write(CMD_MOTOR1, [0, MOTOR_SPEED, 0])
    i2c_write(CMD_MOTOR2, [1, MOTOR_SPEED, 0])


def motor_left():
    """Turn left - right wheel forward, left wheel backward."""
    i2c_write(CMD_MOTOR1, [1, MOTOR_SPEED, 0])
    i2c_write(CMD_MOTOR2, [0, MOTOR_SPEED, 0])


def motor_stop():
    """Stop both motors."""
    i2c_write(CMD_STOP, [0, 0, 0])


def get_distance():
    """Read the ultrasonic sensor to see how far the nearest object is."""
    try:
        bus.write_i2c_block_data(GOPIGO_ADDR, CMD_ULTRASONIC, [15, 0, 0])
        time.sleep(0.5)
        b1 = bus.read_byte(GOPIGO_ADDR)
        time.sleep(0.05)
        b2 = bus.read_byte(GOPIGO_ADDR)
        dist = b1 * 256 + b2
        return dist
    except IOError:
        time.sleep(0.1)
        return 999


def move_with_obstacle_check(direction_func, duration):
    """
    Move in a direction but keep checking for obstacles.
    Stops the motors briefly to read the ultrasonic sensor
    since I2C can only do one thing at a time, then starts
    them again. Returns True if we made it the full distance,
    False if something is blocking the path.
    """
    elapsed = 0

    while elapsed < duration:
        direction_func()
        time.sleep(CHECK_INTERVAL)
        elapsed += CHECK_INTERVAL

        # Pause motors so we can read the sensor without I2C conflicts
        motor_stop()
        time.sleep(0.1)

        dist = get_distance()
        if 0 < dist < OBSTACLE_THRESHOLD:
            print(f"  OBSTACLE detected at {dist}cm!")
            return False

    motor_stop()
    time.sleep(0.3)
    return True


def sim_move(name, duration):
    """Fake movement for simulation mode testing."""
    print(f"  [SIM] Moving {name} for {duration}s")
    time.sleep(duration)
    return True


def send_obstacle_alert(location):
    """Notify the backend that something is blocking the path."""
    try:
        requests.post(
            API_URL + "/api/robot/obstacle",
            json={"blocked": True, "location": location},
            timeout=3,
            verify=False
        )
        print("  Alert sent to dashboard")
    except Exception as e:
        print(f"  Couldn't send alert: {e}")


def wait_for_clearance():
    """Poll the API until the user confirms the path is clear."""
    print("  Waiting for user to confirm path is clear...")

    while True:
        try:
            res = requests.get(
                API_URL + "/api/robot/status",
                timeout=3,
                verify=False
            )
            if res.ok:
                data = res.json()
                if not data.get("blocked", True):
                    print("  Path cleared - continuing patrol")
                    return
        except Exception:
            pass

        time.sleep(2)


def update_location(location):
    """Tell the API where the robot currently is."""
    try:
        requests.post(
            API_URL + "/api/robot/location",
            json={"location": location},
            timeout=3,
            verify=False
        )
    except Exception:
        pass


def run_demo_route(sim_mode):
    """
    Demo route: go straight about 10 feet, turn around, come back.
    The GoPiGo at speed 200 covers roughly 10 feet in 9 seconds.
    Broken into 3 segments so we check for obstacles between each.
    """
    print("\n--- Starting Demo Route ---\n")

    # Reset robot status on the dashboard
    try:
        requests.post(
            API_URL + "/api/robot/obstacle",
            json={"blocked": False, "location": "start"},
            timeout=3,
            verify=False
        )
    except Exception:
        pass

    # Leg 1: go forward ~10 feet in 3 chunks (3 seconds each)
    outbound = [
        ("Outbound - start", 3),
        ("Outbound - midway", 3),
        ("Outbound - end", 3),
    ]

    for name, duration in outbound:
        update_location(name)
        print(f"  Moving: {name}")

        if sim_mode:
            clear = sim_move(name, duration)
        else:
            clear = move_with_obstacle_check(motor_forward, duration)

        if not clear:
            update_location(f"{name} - BLOCKED")
            send_obstacle_alert(name)
            wait_for_clearance()
            # Retry this segment after path is cleared
            print(f"  Retrying: {name}")
            if sim_mode:
                clear = sim_move(name, duration)
            else:
                clear = move_with_obstacle_check(motor_forward, duration)
            if not clear:
                send_obstacle_alert(name)
                wait_for_clearance()

    # Turn around (spin in place for about 2 seconds)
    update_location("Turning around")
    print("  Turning around")
    if not sim_mode:
        motor_right()
        time.sleep(2)
        motor_stop()
        time.sleep(0.5)
    else:
        print("  [SIM] Turning around")
        time.sleep(1)

    # Leg 2: come back the same distance
    returning = [
        ("Return - start", 3),
        ("Return - midway", 3),
        ("Return - end", 3),
    ]

    for name, duration in returning:
        update_location(name)
        print(f"  Moving: {name}")

        if sim_mode:
            clear = sim_move(name, duration)
        else:
            clear = move_with_obstacle_check(motor_forward, duration)

        if not clear:
            update_location(f"{name} - BLOCKED")
            send_obstacle_alert(name)
            wait_for_clearance()
            print(f"  Retrying: {name}")
            if sim_mode:
                clear = sim_move(name, duration)
            else:
                clear = move_with_obstacle_check(motor_forward, duration)
            if not clear:
                send_obstacle_alert(name)
                wait_for_clearance()

    update_location("Home base")
    print("\n--- Demo Route Complete ---\n")


def main():
    print("=" * 40)
    print("HERMES Robot Patrol - Demo Mode")
    print("=" * 40)

    sim_mode = "--sim" in sys.argv

    if not sim_mode:
        if not init_gopigo():
            print("\nGoPiGo not found. Run with --sim to simulate.")
            sys.exit(1)
    else:
        print("Running in SIMULATION mode")

    try:
        run_demo_route(sim_mode)
    except KeyboardInterrupt:
        print("\nPatrol stopped by user")
        if not sim_mode:
            motor_stop()
        sys.exit(0)


if __name__ == "__main__":
    main()