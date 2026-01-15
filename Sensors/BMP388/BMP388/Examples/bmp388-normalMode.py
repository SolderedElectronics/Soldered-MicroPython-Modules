# FILE: bmp388-normalMode.py
# AUTHOR: Borna Biro for soldered.com
# BRIEF: Basic usage example for the BMP388 in normal mode
# WORKS WITH: Pressure & Temperature sensor BMP388 Breakout: www.solde.red/333316
# LAST UPDATED: 2025-01-15

from machine import Pin, I2C
from bmp388 import BMP388
from bmp388_constants import TIME_STANDBY_1280MS
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# bmp388 = BMP388(i2c)

# Initialize sensor over Qwiic
bmp388 = BMP388()

# Set sea level pressure for accurate altitude readings
bmp388.setSeaLevelPressure(1025.0)

# Set standby time to roughly 1.3 seconds
bmp388.setTimeStandby(TIME_STANDBY_1280MS)

# Start continuous measurement in normal mode
bmp388.startNormalConversion()

while True:
    temperature, pressure, altitude = bmp388.getMeasurements()
    if temperature is not None:
        print("{:.2f}*C   {:.2f}hPa   {:.2f}m".format(temperature, pressure, altitude))
    time.sleep(0.25)
