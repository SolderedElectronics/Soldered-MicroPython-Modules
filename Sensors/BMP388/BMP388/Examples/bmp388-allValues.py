# FILE: bmp388-allValues.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example for the BMP388 sensor that reads temperature, pressure
#        and calculates the altitude using the pressure measurement
# WORKS WITH: Pressure & Temperature sensor BMP388 Breakout: www.solde.red/333316
# LAST UPDATED: 2025-01-XX
from machine import Pin, I2C
from bmp388 import BMP388
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# bmp388 = BMP388(i2c)

# Initialize sensor over Qwiic
bmp388 = BMP388()

# Set sea level pressure for accurate altitude readings (adjust to your local value)
bmp388.setSeaLevelPressure(1013.25)

# Start continuous measurement in normal mode
bmp388.startNormalConversion()

# Wait a bit for the first measurement to be ready
# (depends on oversampling settings, give it extra time)
time.sleep(0.5)

# Infinite loop
while 1:
    # Variables for storing measurement data (matching Arduino example)
    temperature, pressure, altitude = bmp388.getMeasurements()

    # Check if the data is ready (matching Arduino: if (bmp388.getMeasurements(...)))
    if temperature is not None:
        # Print the results (matching Arduino format)
        print("{:.2f}*C   {:.2f}hPa   {:.2f}m".format(temperature, pressure, altitude))
    # Note: Arduino example doesn't print "waiting" message, it just silently waits

    # Wait a little bit (matching Arduino: delay(250))
    time.sleep(0.25)
