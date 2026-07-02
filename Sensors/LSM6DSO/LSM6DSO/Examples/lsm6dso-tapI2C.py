# FILE: lsm6dso-tapI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Use LSM6DSO single-tap detection via hardware interrupt (INT1)
# LAST UPDATED: 2026-07-02
#
# Wire the sensor's INT1 pin to the GPIO below (active high, push-pull).

from lsm6dso import LSM6DSO
from machine import Pin

INT_PIN = Pin(5, Pin.IN)

imu = LSM6DSO()
imu.enableAccelerator()
imu.enableSingleTapDetection()

while True:
    if INT_PIN.value():
        status = imu.getEventStatus()
        if status["tap"]:
            print("Single Tap Detected!")
