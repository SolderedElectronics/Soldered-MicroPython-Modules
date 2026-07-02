# FILE: lsm6ds3-doubleTapI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Use LSM6DS3 double-tap detection via hardware interrupt (INT1)
# LAST UPDATED: 2026-07-02
#
# Wire the sensor's INT1 pin to the GPIO below (active high, push-pull).

from lsm6ds3 import LSM6DS3
from machine import Pin

INT_PIN = Pin(5, Pin.IN)

imu = LSM6DS3()
imu.enableAccelerator()
imu.enableDoubleTapDetection()

while True:
    if INT_PIN.value():
        status = imu.getEventStatus()
        if status["doubleTap"]:
            print("Double Tap Detected!")
