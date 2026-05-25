# FILE: SimpleSensor-lightI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Simple Light Sensor example using easyC (I2C) mode
# WORKS WITH: Simple Light Sensor easyC: www.solde.red/333012
# LAST UPDATED: 2026-05-25

from SimpleLightSensor import SimpleLightSensor
import time

# Initialize sensor in easyC mode
# I2C auto-detected on pins 21 (SDA) / 22 (SCL) on ESP32
# For a different I2C address (0x30-0x37), pass address parameter:
# sensor = SimpleLightSensor(address=0x31)
sensor = SimpleLightSensor()

# Optional: adjust detection threshold (default 50%)
# sensor.setThreshold(30.0)

# Optional: invert the onboard LED behavior
# sensor.invertLED(True)

# Calibration: expose sensor to the maximum light level you want as 100%,
# note the getValue() reading, then call calibrate() with that value
# sensor.calibrate(90.0)

while True:
    raw = sensor.getRawReading()
    value = sensor.getValue()
    light = sensor.isLightDetected()

    print("Raw: {:4d}  Light%: {:6.2f}%  Light detected: {}".format(raw, value, light))
    time.sleep(1)
