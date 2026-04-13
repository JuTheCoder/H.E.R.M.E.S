# HERMES - Command Reference Sheet

Pi Username: hermes
Pi Hostname: raspberrypi.local (works on any network - no need to find IP)
Dashboard URL: https://raspberrypi.local:8000
Login: admin / hermes2026 (admin) or user / hermes (viewer)


## Connecting to the Pi

SSH from your Mac (works on any network):

    ssh hermes@raspberrypi.local

If raspberrypi.local doesnt work, find the IP:

    On iPhone hotspot: Settings > Personal Hotspot > look at connected devices
    On Pi directly: hostname -I

VNC remote desktop (start the server on the Pi first):

    tightvncserver :1

Then on Mac, open Finder > Cmd+K and type:

    vnc://raspberrypi.local:5901


## Starting Everything Up

You need 3 terminals on the Pi (either SSH sessions or VNC terminal windows).
Start them in this order.

### Terminal 1 - Start the API server

    cd ~/HERMES/backend
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem

### Terminal 2 - Start the sensor reader

    cd ~/HERMES/backend
    python3 serial_reader.py

### Terminal 3 - Run the robot patrol

    cd ~/HERMES/robot_control
    python3 patrol.py

To run patrol in simulation mode (no robot needed):

    python3 patrol.py --sim


## Stopping Things

Stop any running script: Ctrl + C

Emergency stop the GoPiGo motors manually:

    python3 -c "import smbus; bus = smbus.SMBus(1); bus.write_i2c_block_data(0x08, 120, [0,0,0]); print('stopped')"


## Dashboard Access

Open a browser on any device connected to the same network and go to:

    https://raspberrypi.local:8000

Accept the security warning about the self-signed certificate (Advanced > Proceed).
Use Chrome not Safari if you have issues.

Admin panel for changing thresholds and managing users:

    https://raspberrypi.local:8000/admin.html


## Demo Day Quick Start (Hotspot)

1. Turn on your phone's hotspot
2. Put 8 AA batteries in the GoPiGo
3. Mount Pi on GoPiGo, plug in USB-C power bank
4. Plug sensor Arduino into Pi USB port
5. Wait ~1 minute for Pi to boot and auto-connect to hotspot
6. Connect your Mac to the same hotspot
7. SSH in: ssh hermes@raspberrypi.local
8. Start VNC if you want desktop: tightvncserver :1
9. Open 3 terminals and run:
   - Terminal 1: cd ~/HERMES/backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
   - Terminal 2: cd ~/HERMES/backend && python3 serial_reader.py
   - Terminal 3: cd ~/HERMES/robot_control && python3 patrol.py
10. Open dashboard on Mac: https://raspberrypi.local:8000
11. Accept the certificate warning
12. Log in as admin/hermes2026
13. Watch sensor data flow in, robot patrol, obstacle detection, WhatsApp alerts


## Testing Individual Components

### Test the sensor Arduino is sending data

    cd ~/HERMES/backend
    python3 -c "import serial, time; s = serial.Serial('/dev/ttyACM0', 9600, timeout=2); time.sleep(2); print(s.readline().decode())"

### Test the GoPiGo motors

Forward for 2 seconds then stop:

    python3 -c "
    import smbus, time
    bus = smbus.SMBus(1)
    addr = 0x08
    bus.write_i2c_block_data(addr, 111, [0, 200, 0])
    bus.write_i2c_block_data(addr, 112, [0, 200, 0])
    time.sleep(2)
    bus.write_i2c_block_data(addr, 120, [0,0,0])
    print('Done')
    "

### Test the ultrasonic sensor

    python3 -c "
    import smbus, time
    bus = smbus.SMBus(1)
    bus.write_i2c_block_data(0x08, 117, [15,0,0])
    time.sleep(0.5)
    b1 = bus.read_byte(0x08)
    b2 = bus.read_byte(0x08)
    print('Distance:', b1 * 256 + b2, 'cm')
    "

### Test WhatsApp alert

    cd ~/HERMES/backend
    python3 test_sms.py

### Test obstacle API manually

Set robot as blocked:

    curl -k -X POST https://127.0.0.1:8000/api/robot/obstacle -H "Content-Type: application/json" -d '{"blocked": true, "location": "test"}'

Check robot status:

    curl -k https://127.0.0.1:8000/api/robot/status

Clear the robot path:

    curl -k -X POST https://127.0.0.1:8000/api/robot/clear


## Changing Dashboard Thresholds

From the admin panel in your browser:

    https://raspberrypi.local:8000/admin.html

Log in as admin (admin / hermes2026), adjust the values, and hit save.
The API picks up the new thresholds automatically - no restart needed.

Or edit the thresholds file directly on the Pi:

    nano ~/HERMES/backend/thresholds.json

Then restart the API for changes to take effect (Ctrl+C in Terminal 1, then rerun the uvicorn command).

Note: Dashboard thresholds are separate from Arduino buzzer thresholds.
Dashboard thresholds control what the website shows (safe, moderate, dangerous, etc).
Arduino thresholds control when the physical buzzer goes off.
To change the buzzer thresholds, you have to edit the Arduino code and re-upload (see below).


## Arduino Buzzer Thresholds

These are the values in the Arduino code that trigger the physical buzzer.
To change them, edit the sketch on the Pi:

    nano ~/HERMES/arduino_code/sensors/sensors.ino

Look for these lines near the top:

    #define CO2_DANGER 2000
    #define TEMP_DANGER 95
    #define CO_DANGER 700
    #define AQ_DANGER 70

Change the numbers, save, then compile and upload:

    /home/hermes/HERMES/backend/bin/arduino-cli compile --fqbn arduino:avr:uno ~/HERMES/arduino_code/sensors/
    /home/hermes/HERMES/backend/bin/arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno ~/HERMES/arduino_code/sensors/

IMPORTANT: Stop the serial reader (Ctrl+C in Terminal 2) before uploading to the Arduino. Restart it after the upload finishes.


## Updating Arduino Sensor Code from the Pi

If you need to change sensor thresholds in the Arduino code without unplugging it:

    /home/hermes/HERMES/backend/bin/arduino-cli compile --fqbn arduino:avr:uno ~/HERMES/arduino_code/sensors/
    /home/hermes/HERMES/backend/bin/arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno ~/HERMES/arduino_code/sensors/


## Copying Files from Mac to Pi

    scp ~/Desktop/HERMES/path/to/file hermes@raspberrypi.local:~/HERMES/path/to/file

Example - copy updated patrol.py:

    scp ~/Desktop/HERMES/robot_control/patrol.py hermes@raspberrypi.local:~/HERMES/robot_control/


## Managing Users

From the admin panel in the browser:

    https://raspberrypi.local:8000/admin.html

You can add new users, delete users, and change passwords.
Admin role can change thresholds and manage users.
Viewer role can only see the dashboard.


## WhatsApp Alert Setup

HERMES uses Twilio WhatsApp sandbox for alerts. To set it up from scratch:

1. Create a Twilio account at twilio.com
2. Go to Messaging > Try it out > Send a WhatsApp message
3. Send the join code from your phone to the Twilio WhatsApp number
4. Edit the alert config on the Pi:

    nano ~/HERMES/backend/alert_config.json

5. Fill in your Twilio SID, auth token, the Twilio WhatsApp number, and your phone number


## GoPiGo Motor Reference

The GoPiGo v1 board communicates over I2C at address 0x08.

Motor commands:

    Motor 1 control: command 111, data [direction, speed, 0]
    Motor 2 control: command 112, data [direction, speed, 0]
    Stop all motors: command 120, data [0, 0, 0]
    Ultrasonic read:  command 117, data [15, 0, 0]

Direction: 0 = forward, 1 = backward
Speed: 0-255 (we use 200)

Both motors forward: M1=[0, 200, 0] and M2=[0, 200, 0]
Both motors backward: M1=[1, 200, 0] and M2=[1, 200, 0]
Turn right (spin): M1=[0, 200, 0] and M2=[1, 200, 0]
Turn left (spin):  M1=[1, 200, 0] and M2=[0, 200, 0]


## File Locations on the Pi

    ~/HERMES/backend/main.py          - FastAPI server (API endpoints, auth middleware)
    ~/HERMES/backend/data.py           - Threshold logic and sensor data processing
    ~/HERMES/backend/auth.py           - Login/JWT authentication
    ~/HERMES/backend/alerts.py         - WhatsApp alert system
    ~/HERMES/backend/serial_reader.py  - Reads Arduino serial data and posts to API
    ~/HERMES/backend/thresholds.json   - Configurable dashboard threshold values
    ~/HERMES/backend/users.json        - User accounts
    ~/HERMES/backend/alert_config.json - Twilio/WhatsApp configuration
    ~/HERMES/backend/certs/            - SSL certificates for HTTPS

    ~/HERMES/frontend/index.html       - Main dashboard page
    ~/HERMES/frontend/login.html       - Login page
    ~/HERMES/frontend/admin.html       - Admin panel
    ~/HERMES/frontend/js/dashboard.js  - Dashboard JavaScript
    ~/HERMES/frontend/css/dashboard.css - Dashboard styles

    ~/HERMES/arduino_code/sensors/sensors.ino  - Arduino sensor code
    ~/HERMES/robot_control/patrol.py           - Robot patrol script


## Hardware Connections

Sensor Arduino (Uno R3):
    - Plugged into Pi USB port (shows up as /dev/ttyACM0)
    - DHT22 on pin 7
    - MQ-135 on pin A0
    - MQ-2 on pin A5
    - MH-Z19B CO2 sensor on pins 10 (RX) and 11 (TX)
    - Buzzer on pin 9
    - Alert LED on pin 6

GoPiGo Robot:
    - Pi mounted on GoPiGo board via 26-pin GPIO header (first 26 pins)
    - Communicates over I2C (address 0x08)
    - Ultrasonic sensor plugged into port A1
    - 8 AA batteries power the motors
    - Pi powered separately via USB-C (power bank for portable use)


## Restarting the Pi

    sudo reboot

Wait about a minute then SSH back in.


## Troubleshooting

If the API wont start, check if something is already using port 8000:

    sudo lsof -i :8000

If the serial reader cant connect, check the Arduino is plugged in:

    ls /dev/ttyACM*

If I2C errors happen with the GoPiGo, make sure I2C is enabled:

    sudo raspi-config
    (Interface Options > I2C > Enable)

If the GoPiGo board isnt detected:

    sudo i2cdetect -y 1
    (should show device at address 0x08)

If VNC wont start:

    tightvncserver -kill :1
    tightvncserver :1

If dashboard loads but shows no sensor data, make sure both the API (Terminal 1) AND serial reader (Terminal 2) are running.

If WhatsApp alerts arent sending, check the config:

    cat ~/HERMES/backend/alert_config.json

If motors spin but wheels dont move, push the wheels firmly onto the motor shafts.

If cant SSH into Pi, the Pi didnt connect to hotspot. Either:
    - Check your phone hotspot for connected devices to find the IP
    - Or plug a keyboard into the Pi and type blind:
      sudo nmcli device wifi connect "YOUR_HOTSPOT" password "YOUR_PASSWORD"
