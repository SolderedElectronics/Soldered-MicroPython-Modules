# FILE: lsm6dso-tiltI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Use LSM6DSO tilt detection via hardware interrupt (INT1)
# LAST UPDATED: 2026-07-02
#
# Wire the sensor's INT1 pin to the GPIO below (active high, push-pull).

from lsm6dso import LSM6DSO
from machine import Pin

INT_PIN = Pin(5, Pin.IN)

imu = LSM6DSO()
imu.enableAccelerator()
imu.enableTiltDetection()

while True:
    if INT_PIN.value():
        status = imu.getEventStatus()
        if status["tilt"]:
            print("Tilt Detected!")
