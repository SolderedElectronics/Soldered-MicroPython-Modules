# FILE: bmp388-forcedMeasurement.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Forced measurement example for the BMP388
# WORKS WITH: Pressure & Temperature sensor BMP388 Breakout: www.solde.red/333316
# LAST UPDATED: 2025-01-15

from machine import Pin, I2C
from bmp388 import BMP388
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# bmp388 = BMP388(i2c)

# Initialize sensor over Qwiic
bmp388 = BMP388()

# Set sea level pressure for accurate altitude readings
bmp388.setSeaLevelPressure(1025.0)

while True:
    # Request a new measurement
    bmp388.startForcedConversion()

    # Wait until data is ready
    while True:
        temperature, pressure, altitude = bmp388.getMeasurements()
        if temperature is not None:
            print("{:.2f}*C   {:.2f}hPa   {:.2f}m".format(temperature, pressure, altitude))
            break
        time.sleep(0.02)

    # Wait a little bit before next measurement
    time.sleep(1)
