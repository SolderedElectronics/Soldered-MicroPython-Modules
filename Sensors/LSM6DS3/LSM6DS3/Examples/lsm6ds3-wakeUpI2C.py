# FILE: lsm6ds3-wakeUpI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Use LSM6DS3 wake-up detection via hardware interrupt (INT2)
# LAST UPDATED: 2026-07-02
#
# Wire the sensor's INT2 pin to the GPIO below (active high, push-pull).

from lsm6ds3 import LSM6DS3
from machine import Pin

INT_PIN = Pin(5, Pin.IN)

imu = LSM6DS3()
imu.enableAccelerator()
imu.enableWakeUpDetection()

while True:
    if INT_PIN.value():
        status = imu.getEventStatus()
        if status["wakeUp"]:
            print("Wake up Detected!")
