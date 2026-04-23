# FILE: ak09918-compassHeading.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Calculate a compass heading from AK09918 X and Y readings and print
#        the heading in degrees along with the nearest cardinal direction
# WORKS WITH: 3-Axis Digital Compass AK09918 breakout: www.solde.red/333392
# LAST UPDATED: 2026-04-23

# The heading is computed with atan2(Y, X), which gives the angle of the
# horizontal magnetic field vector relative to the sensor's X axis.
# IMPORTANT: keep the board flat (horizontal) while testing — tilting
# introduces error because the vertical component of Earth's field leaks
# into X and Y. Full tilt compensation requires a separate accelerometer.

from machine import Pin, I2C
from ak09918 import AK09918
from ak09918_constants import AK09918_CONT_MEASURE_MODE1, AK09918_ERR_OK
import math
import time


def headingLabel(deg):
    """Return the nearest cardinal/intercardinal label for a 0-360 degree heading."""
    if deg < 22.5 or deg >= 337.5:
        return "N"
    if deg < 67.5:
        return "NE"
    if deg < 112.5:
        return "E"
    if deg < 157.5:
        return "SE"
    if deg < 202.5:
        return "S"
    if deg < 247.5:
        return "SW"
    if deg < 292.5:
        return "W"
    return "NW"


# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# compass = AK09918(i2c, mode=AK09918_CONT_MEASURE_MODE1)

# Initialize sensor over Qwiic in 10 Hz continuous measurement mode
compass = AK09918(mode=AK09918_CONT_MEASURE_MODE1)

print("AK09918 compass heading - keep the board flat!")
print("Heading\t\tDirection\tX\t\tY\t\tZ")

# Infinite loop
while True:
    if compass.isDataReady() != AK09918_ERR_OK:
        continue

    err, x, y, z = compass.getData()
    if err != AK09918_ERR_OK:
        print("Read error: {}".format(compass.strError(err)))
        continue

    # atan2 returns radians in range -pi to +pi; convert to 0-360 degrees
    heading = math.atan2(y, x) * 180.0 / math.pi
    if heading < 0.0:
        heading += 360.0

    print("{:.1f}\t\t{}\t\t{}\t\t{}\t\t{}".format(heading, headingLabel(heading), x, y, z))

    time.sleep_ms(200)
