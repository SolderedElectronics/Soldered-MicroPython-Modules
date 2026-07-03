"""
SelfTestFactoryReset.py - Run the SCD43's built-in self-test and optionally
perform a factory reset.

The self-test verifies sensor hardware integrity and is useful as an
end-of-line production test. It takes approximately 10 seconds to complete.

The factory reset erases all EEPROM settings and calibration history,
returning the sensor to its original factory state. Use it when a sensor
needs to be recalibrated from scratch. It takes approximately 1200 ms.

Hardware connections:
  - Connect the SCD43 breakout to your board via the Qwiic / I2C connector.
"""

from machine import I2C, Pin
import time
from scd43 import SCD43

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = SCD43()

print("SCD43 - Self Test and Factory Reset")

if not sensor.begin(i2c):
    print("Sensor not found. Check wiring. Halting.")
    raise SystemExit

# Both commands require idle mode.
if not sensor.stopPeriodicMeasurement():
    print("Could not stop periodic measurement. Halting.")
    raise SystemExit

# --- Self test ---
# This blocks for ~10 seconds.
print("Running self-test (this takes ~10 seconds)...")

if sensor.performSelfTest():
    print("Self-test passed. Sensor is functioning correctly.")
else:
    print("Self-test failed. The sensor may be damaged.")

# --- Factory reset ---
# Uncomment to erase all settings and calibration data.
# WARNING: this cannot be undone.
#
# print("Performing factory reset (~1200 ms)...")
# if sensor.performFactoryReset():
#     print("Factory reset complete.")
# else:
#     print("Factory reset failed.")

# Nothing further to do.
