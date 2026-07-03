# FILE: SimpleSensor-rainI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Simple Rain Sensor example using easyC (I2C) mode
# WORKS WITH: Simple Rain Sensor easyC: www.solde.red/333010
# LAST UPDATED: 2026-05-25

from SimpleRainSensor import SimpleRainSensor
import time

# Initialize sensor in easyC mode
# I2C auto-detected on pins 21 (SDA) / 22 (SCL) on ESP32
# For a different I2C address (0x30-0x37), pass address parameter:
# sensor = SimpleRainSensor(address=0x31)
sensor = SimpleRainSensor()

# Optional: adjust detection threshold (default 50%)
# sensor.setThreshold(60.0)

# Optional: invert the onboard LED behavior
# sensor.invertLED(True)

# Calibration: submerge sensor completely in water,
# note the getValue() reading, then call calibrate() with that value
# sensor.calibrate(85.0)

while True:
    raw = sensor.getRawReading()
    value = sensor.getValue()
    raining = sensor.isRaining()

    print("Raw: {:4d}  Rain%: {:6.2f}%  Raining: {}".format(raw, value, raining))
    time.sleep(1)
