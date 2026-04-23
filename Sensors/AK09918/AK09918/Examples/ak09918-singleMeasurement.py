# FILE: ak09918-singleMeasurement.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Take one magnetic field measurement at a time using AK09918
#        single-measurement (NORMAL) mode
# WORKS WITH: 3-Axis Digital Compass AK09918 breakout: www.solde.red/333392
# LAST UPDATED: 2026-04-23

# In single-measurement mode the sensor powers itself down after each reading.
# getData() triggers the measurement and blocks until it is complete, so no
# polling loop is needed. This mode is ideal for battery-powered applications.

from machine import Pin, I2C
from ak09918 import AK09918
from ak09918_constants import (
    AK09918_NORMAL,
    AK09918_ERR_OK,
    AK09918_ERR_TIMEOUT,
    AK09918_ERR_OVERFLOW,
)
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# compass = AK09918(i2c, mode=AK09918_NORMAL)

# Initialize sensor in single-measurement mode
compass = AK09918(mode=AK09918_NORMAL)

print("AK09918 ready - single-measurement mode")
print("One reading per second")
print("X (uT*10)\tY (uT*10)\tZ (uT*10)")

# Infinite loop
while True:
    # getData() triggers the measurement and blocks (~1 ms) until done
    err, x, y, z = compass.getData()

    if err == AK09918_ERR_TIMEOUT:
        print("Timeout - sensor did not respond")
    elif err == AK09918_ERR_OVERFLOW:
        print("Overflow - field too strong to measure")
    elif err != AK09918_ERR_OK:
        print("Error: {}".format(compass.strError(err)))
    else:
        # Print the X, Y, Z values
        print("{}\t\t{}\t\t{}".format(x, y, z))

    time.sleep(1)
