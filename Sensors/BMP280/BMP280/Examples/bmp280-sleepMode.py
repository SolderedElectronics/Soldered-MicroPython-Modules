# FILE: bmp280-sleepMode.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Sleep mode example with manual wake for a single measurement
# WORKS WITH: Pressure & Temperature sensor BMP280 Breakout
# LAST UPDATED: 2025-01-15

from machine import Pin, I2C
from bmp280 import BMP280

# Import constants from separate file to keep examples stable if defaults change.
from bmp280_constants import (
    SLEEP_MODE,
    FORCED_MODE,
    OVERSAMPLING_X1,
    IIR_FILTER_OFF,
)
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# bmp280 = BMP280(i2c)

# Initialize sensor over Qwiic
bmp280 = BMP280()

# Configure low-power sampling
bmp280.setOversampling(
    presOversampling=OVERSAMPLING_X1, tempOversampling=OVERSAMPLING_X1
)
bmp280.setIIRFilter(IIR_FILTER_OFF)
bmp280.setMode(SLEEP_MODE)

while True:
    # Wake up for a single measurement
    bmp280.setMode(FORCED_MODE)
    time.sleep(0.05)

    temperature, pressure, altitude = bmp280.getMeasurements()
    print("{:.2f}*C   {:.2f}hPa   {:.2f}m".format(temperature, pressure, altitude))

    # Back to sleep between samples
    bmp280.setMode(SLEEP_MODE)
    time.sleep(2)
