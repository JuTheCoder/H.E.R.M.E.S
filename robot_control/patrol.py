"""
HERMES Robot Patrol
Robot goes forward about 2 feet, turns around, comes back,
and keeps looping until stopped from the dashboard or ctrl+c.
If something blocks the path it stops, sends a WhatsApp alert,
and waits for the user to hit clear path on the dashboard.

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

# How long to drive before checking the sensor (seconds)
CHECK_INTERVAL = 0.8

# Motor speed (0-255, maxing it out)
MOTOR_SPEED = 255

# I2C command bytes for GoPiGo v1 firmware
CMD_MOTOR1 = 111
CMD_MOTOR2 = 112
CMD_STOP = 120
CMD_ULTRASONIC = 117

# How long to drive for ~2 feet (seconds)
LEG_DURATION = 2


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
    i2c_write(CMD_MOTOR1, [1, MOTOR_SPEED, 0])
    i2c_write(CMD_MOTOR2, [1, MOTOR_SPEED, 0])


def motor_backward():
    """Both wheels backward."""
    i2c_write(CMD_MOTOR1, [0, MOTOR_SPEED, 0])
    i2c_write(CMD_MOTOR2, [0, MOTOR_SPEED, 0])


def motor_right():
    """Turn right in place."""
    i2c_write(CMD_MOTOR1, [1, MOTOR_SPEED, 0])
    i2c_write(CMD_MOTOR2, [0, MOTOR_SPEED, 0])


def motor_left():
    """Turn left in place."""
    i2c_write(CMD_MOTOR1, [0, MOTOR_SPEED, 0])
    i2c_write(CMD_MOTOR2, [1, MOTOR_SPEED, 0])


def motor_stop():
    """Stop both motors."""
    i2c_write(CMD_STOP, [0, 0, 0])


def get_distance():
    """Read the ultrasonic sensor to see how far the nearest object is."""
    try:
        bus.write_i2c_block_data(GOPIGO_ADDR, CMD_ULTRASONIC, [15, 0, 0])
        time.sleep(0.2)
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
    Has to stop briefly to read the ultrasonic sensor
    since I2C can only do one thing at a time.
    """
    elapsed = 0

    while elapsed < duration:
        direction_func()
        time.sleep(CHECK_INTERVAL)
        elapsed += CHECK_INTERVAL

        # Quick pause to read sensor
        motor_stop()
        time.sleep(0.05)

        dist = get_distance()
        if 0 < dist < OBSTACLE_THRESHOLD:
            print(f"  OBSTACLE at {dist}cm!")
            return False

    motor_stop()
    time.sleep(0.2)
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
    """Poll the API until the user hits clear path on the dashboard."""
    print("  Waiting for clear path...")

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
                    print("  Path cleared")
                    return
        except Exception:
            pass

        time.sleep(2)


def check_if_stopped():
    """Check if the user hit stop on the dashboard."""
    try:
        res = requests.get(
            API_URL + "/api/robot/status",
            timeout=2,
            verify=False
        )
        if res.ok:
            data = res.json()
            return not data.get("running", False)
    except Exception:
        pass
    return False


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


def run_patrol(sim_mode):
    """
    Patrol loop: go forward ~2 feet, turn around, repeat.
    Keeps going until stopped from dashboard or ctrl+c.
    """
    print("\n--- Starting Patrol ---\n")

    # Reset status
    try:
        requests.post(
            API_URL + "/api/robot/obstacle",
            json={"blocked": False, "location": "start"},
            timeout=3,
            verify=False
        )
    except Exception:
        pass

    lap = 0

    while True:
        # Check if user hit stop
        if check_if_stopped():
            update_location("stopped")
            print("  Stopped from dashboard")
            motor_stop()
            # Wait until started again
            while check_if_stopped():
                time.sleep(2)
            print("  Resuming patrol")

        lap += 1
        print(f"\n  Lap {lap} - going out")
        update_location(f"Lap {lap} - outbound")

        if sim_mode:
            clear = sim_move("forward", LEG_DURATION)
        else:
            clear = move_with_obstacle_check(motor_forward, LEG_DURATION)

        if not clear:
            update_location(f"Lap {lap} - BLOCKED")
            send_obstacle_alert(f"Lap {lap} - outbound")
            wait_for_clearance()
            # Try again after cleared
            if sim_mode:
                sim_move("forward retry", LEG_DURATION)
            else:
                move_with_obstacle_check(motor_forward, LEG_DURATION)

        # Turn around
        update_location(f"Lap {lap} - turning")
        print(f"  Lap {lap} - turning around")
        if not sim_mode:
            motor_right()
            time.sleep(1.5)
            motor_stop()
            time.sleep(0.3)
        else:
            print("  [SIM] Turning")
            time.sleep(0.5)

        # Head back
        print(f"  Lap {lap} - coming back")
        update_location(f"Lap {lap} - return")

        if sim_mode:
            clear = sim_move("return", LEG_DURATION)
        else:
            clear = move_with_obstacle_check(motor_forward, LEG_DURATION)

        if not clear:
            update_location(f"Lap {lap} - BLOCKED")
            send_obstacle_alert(f"Lap {lap} - return")
            wait_for_clearance()
            if sim_mode:
                sim_move("return retry", LEG_DURATION)
            else:
                move_with_obstacle_check(motor_forward, LEG_DURATION)

        # Turn around again to face original direction
        update_location(f"Lap {lap} - turning back")
        if not sim_mode:
            motor_right()
            time.sleep(1.5)
            motor_stop()
            time.sleep(0.3)
        else:
            print("  [SIM] Turning back")
            time.sleep(0.5)

        update_location("Home base")
        print(f"  Lap {lap} done\n")


def main():
    print("=" * 40)
    print("HERMES Robot Patrol")
    print("=" * 40)

    sim_mode = "--sim" in sys.argv

    if not sim_mode:
        if not init_gopigo():
            print("\nGoPiGo not found. Run with --sim to simulate.")
            sys.exit(1)
    else:
        print("Running in SIMULATION mode")

    # Wait for start signal from dashboard
    print("Waiting for start from dashboard...")
    while True:
        try:
            res = requests.get(API_URL + "/api/robot/status", timeout=2, verify=False)
            if res.ok and res.json().get("running", False):
                break
        except Exception:
            pass
        time.sleep(2)

    try:
        run_patrol(sim_mode)
    except KeyboardInterrupt:
        print("\nPatrol stopped")
        if not sim_mode:
            motor_stop()
        update_location("idle")
        sys.exit(0)


if __name__ == "__main__":
    main()
