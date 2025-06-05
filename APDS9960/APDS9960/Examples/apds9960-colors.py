# FILE: APDS9960-colors.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example of measuring the colors detected by the sensor in form of RGB values from 0 to 255 for each color
# WORKS WITH: Color and gesture sensor APDS-9960 breakout: www.solde.red/333002
# LAST UPDATED: 2025-06-05

from time import sleep

from machine import Pin, I2C
import machine

from apds9960 import *

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(sda=Pin(21), scl=Pin(22))
# apds = APDS9960(i2c)

# Initialize sensor over Qwiic
apds = APDS9960()

print("Light Sensor Test")
print("=================")
apds.enableLightSensor()

while True:
    # Pause for 500ms between each measurement
    sleep(0.5)
    # Print out the color RGB values, ranges from 0 to 255
    print(
        "R={} G={} B={}".format(
            apds.readRedLight(), apds.readGreenLight(), apds.readBlueLight()
        )
    )
