# FILE: lsm6dso-wakeUpI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Use LSM6DSO wake-up detection via hardware interrupt (INT1)
# LAST UPDATED: 2026-07-02
#
# Wire the sensor's INT1 pin to the GPIO below (active high, push-pull).

from lsm6dso import LSM6DSO
from machine import Pin

INT_PIN = Pin(5, Pin.IN)

imu = LSM6DSO()
imu.enableAccelerator()
imu.enableWakeUpDetection()

while True:
    if INT_PIN.value():
        status = imu.getEventStatus()
        if status["wakeUp"]:
            print("Wake up Detected!")
