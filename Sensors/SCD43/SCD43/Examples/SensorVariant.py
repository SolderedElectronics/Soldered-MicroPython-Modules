"""
SensorVariant.py - Read the SCD4x sensor variant identifier and serial number.

The Sensirion SCD4x family includes the SCD40, SCD41, SCD42, and SCD43.
This example reads the variant code reported by the sensor to confirm which
model is connected, and also prints the unique 48-bit serial number.

Hardware connections:
  - Connect the SCD43 breakout to your board via the Qwiic / I2C connector.
"""

from machine import I2C, Pin
import time
from scd43 import SCD43, VARIANT_SCD40, VARIANT_SCD41, VARIANT_SCD42, VARIANT_SCD43

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = SCD43()

print("SCD43 - Sensor Variant and Serial Number")

if not sensor.begin(i2c):
    print("Sensor not found. Check wiring. Halting.")
    raise SystemExit

# Both commands require idle mode — stop periodic measurements first.
if not sensor.stopPeriodicMeasurement():
    print("Could not stop periodic measurement. Halting.")
    raise SystemExit

# Read and display the sensor variant.
variant = sensor.getSensorVariant()
variant_names = {
    VARIANT_SCD40: "SCD40",
    VARIANT_SCD41: "SCD41",
    VARIANT_SCD42: "SCD42",
    VARIANT_SCD43: "SCD43",
}
print(
    "Sensor variant:", variant_names.get(variant, "Unknown (0x{:04X})".format(variant))
)

# Read and display the unique serial number.
serial = sensor.getSerialNumber()
if serial is not None:
    print("Serial number: 0x{:012X}".format(serial))
else:
    print("Failed to read serial number.")
