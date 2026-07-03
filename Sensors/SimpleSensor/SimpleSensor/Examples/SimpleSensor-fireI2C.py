# FILE: SimpleSensor-fireI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Simple Fire Sensor example using easyC (I2C) mode
# WORKS WITH: Simple Fire Sensor easyC: www.solde.red/333013
# LAST UPDATED: 2026-05-25

from SimpleFireSensor import SimpleFireSensor
import time

# Initialize sensor in easyC mode
# I2C auto-detected on pins 21 (SDA) / 22 (SCL) on ESP32
# For a different I2C address (0x30-0x37), pass address parameter:
# sensor = SimpleFireSensor(address=0x31)
sensor = SimpleFireSensor()

# Optional: adjust detection threshold (default 50%)
# sensor.setThreshold(40.0)

# Optional: invert the onboard LED behavior
# sensor.invertLED(True)

# Calibration: expose sensor to a flame at the detection distance you want as 100%,
# note the getValue() reading, then call calibrate() with that value
# sensor.calibrate(80.0)

while True:
    raw = sensor.getRawReading()
    value = sensor.getValue()
    fire = sensor.isFireDetected()

    print("Raw: {:4d}  Fire%: {:6.2f}%  Fire detected: {}".format(raw, value, fire))
    time.sleep(1)
