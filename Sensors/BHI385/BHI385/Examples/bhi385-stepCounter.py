# FILE: bhi385-stepCounter.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Count footsteps using the Bosch BHI385 Smart IMU step counter virtual
#        sensor (sensor ID 52). The step counter outputs a cumulative step count
#        that increments as the sensor detects walking/running. The count is
#        retained across sensor enable/disable cycles but resets on power-off.
# WORKS WITH: Bosch BHI385 Smart IMU breakout: www.solde.red/333232
# LAST UPDATED: 2026-04-15

from machine import Pin, I2C
from bhi385 import BHI385, BHI385_I2C_ADDR_HIGH
import time

SCL_PIN = 22
SDA_PIN = 21

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
imu = BHI385(i2c, BHI385_I2C_ADDR_HIGH)

print("BHI385 Step Counter example")

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

# Enable step counter at 100 Hz
if not imu.enableStepCounter(100.0):
    print("ERROR: Failed to enable step counter.")
    raise SystemExit
print("Step counter enabled: 100 Hz")

imu.disableDebug()

print()
print("Walk around to count steps.")
print("Steps")

while True:
    imu.update()

    if imu.stepUpdated():
        print(imu.getStepCount())

    imu.clearUpdatedFlags()
    time.sleep_ms(100)
