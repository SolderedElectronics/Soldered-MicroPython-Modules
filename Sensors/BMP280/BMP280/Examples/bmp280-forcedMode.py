# FILE: bmp280-forcedMode.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: One-shot measurements in forced mode with custom sampling
# WORKS WITH: Pressure & Temperature sensor BMP280 Breakout
# LAST UPDATED: 2025-01-15

from machine import Pin, I2C
from bmp280 import BMP280

# Import constants from separate file to keep examples stable if defaults change.
from bmp280_constants import (
    FORCED_MODE,
    OVERSAMPLING_X8,
    OVERSAMPLING_X2,
    IIR_FILTER_2,
)
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# bmp280 = BMP280(i2c)

# Initialize sensor over Qwiic
bmp280 = BMP280()

# Configure sampling rates and filter
bmp280.setOversampling(
    presOversampling=OVERSAMPLING_X8, tempOversampling=OVERSAMPLING_X2
)
bmp280.setIIRFilter(IIR_FILTER_2)
bmp280.setMode(FORCED_MODE)
while True:
    temperature, pressure, altitude = bmp280.getMeasurements()
    print("{:.2f}*C   {:.2f}hPa   {:.2f}m".format(temperature, pressure, altitude))
    time.sleep(1)
