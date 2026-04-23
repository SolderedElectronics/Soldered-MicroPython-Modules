# FILE: ak09918-selfTest.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Run the AK09918's built-in hardware self-test to verify the sensor
#        is working correctly
# WORKS WITH: 3-Axis Digital Compass AK09918 breakout: www.solde.red/333392
# LAST UPDATED: 2026-04-23

# The self-test energises an internal coil that applies a known magnetic field
# to the sensing elements. The driver checks that the resulting X, Y, Z outputs
# fall within the limits defined in the datasheet:
#   X: -200 to +200 counts
#   Y: -200 to +200 counts
#   Z: -1000 to -150 counts
# Run this once after assembly to confirm the sensor is functional.

from machine import Pin, I2C
from ak09918 import AK09918
from ak09918_constants import AK09918_ERR_OK

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# compass = AK09918(i2c)

# Initialize sensor in power-down; selfTest() manages mode transitions itself
compass = AK09918()

device_id = compass.getDeviceID()
print("Device ID: 0x{:04X}".format(device_id))
# Expected: 0x480A (company ID 0x48, device ID 0x0A)

print("Running self-test...")
err = compass.selfTest()

if err == AK09918_ERR_OK:
    print("Self-test PASSED")
else:
    print("Self-test FAILED: {}".format(compass.strError(err)))
