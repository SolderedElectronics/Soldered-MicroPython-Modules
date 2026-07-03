# FILE: SimpleSensor-soilI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Simple Soil Humidity Sensor example using easyC (I2C) mode
# WORKS WITH: Simple Soil Humidity Sensor easyC: www.solde.red/333011
# LAST UPDATED: 2026-05-25

from SimpleSoilSensor import SimpleSoilSensor
import time

# Initialize sensor in easyC mode
# I2C auto-detected on pins 21 (SDA) / 22 (SCL) on ESP32
# For a different I2C address (0x30-0x37), pass address parameter:
# sensor = SimpleSoilSensor(address=0x31)
sensor = SimpleSoilSensor()

# Optional: adjust detection threshold (default 50%)
# sensor.setThreshold(40.0)

# Optional: invert the onboard LED behavior
# sensor.invertLED(True)

# Calibration: insert sensor completely into moist soil or water,
# note the getValue() reading, then call calibrate() with that value
# sensor.calibrate(85.0)

while True:
    raw = sensor.getRawReading()
    value = sensor.getValue()
    moist = sensor.isMoist()

    print("Raw: {:4d}  Moisture%: {:6.2f}%  Moist: {}".format(raw, value, moist))
    time.sleep(1)
