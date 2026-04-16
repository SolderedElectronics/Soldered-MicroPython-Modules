# FILE: bhi385-doubleTap.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Detect double taps using the Bosch BHI385 Smart IMU multi-tap virtual
#        sensor (sensor ID 153). Tap the board/sensor twice in quick succession
#        to trigger a detection. The firmware's double-tap algorithm requires
#        two sharp acceleration impulses within a short time window.
# WORKS WITH: Bosch BHI385 Smart IMU breakout: www.solde.red/333232
# LAST UPDATED: 2026-04-15

from machine import Pin, I2C
from bhi385 import BHI385, BHI385_I2C_ADDR_HIGH, BHI385_TAP_DOUBLE
import time

SCL_PIN = 22
SDA_PIN = 21

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
imu = BHI385(i2c, BHI385_I2C_ADDR_HIGH)

print("BHI385 Double Tap Detection example")

if not imu.begin():
    print("ERROR: BHI385 not found! Check wiring.")
    raise SystemExit

imu.enableDebug()

print("Loading firmware...")
with open("bhi385_firmware.bin", "rb") as f:
    firmware = f.read()

if not imu.loadFirmware(firmware):
    print("Firmware load failed.")
    raise SystemExit
print("Firmware loaded successfully.")

# Enable multi-tap sensor configured for double-tap-only detection at 100 Hz
if not imu.enableMultiTapDetect(BHI385_TAP_DOUBLE, 100.0):
    print("ERROR: Failed to enable multi-tap sensor.")
    raise SystemExit
print("Double tap detection enabled.")

imu.disableDebug()

print()
print("Tap the sensor twice quickly to detect a double tap.")
print("Count  Type")

tap_count = 0

# Poll without delay — tap events are instantaneous and the FIFO should be
# drained as quickly as possible after the interrupt fires.
while True:
    imu.update()

    if imu.tapUpdated() and imu.getTapType() == BHI385_TAP_DOUBLE:
        tap_count += 1
        print("{}      Double tap".format(tap_count))

    imu.clearUpdatedFlags()
