# FILE: lsm6ds3-pedometerI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Use LSM6DS3 pedometer via hardware interrupt (INT1) and periodic polling
# LAST UPDATED: 2026-07-02
#
# Wire the sensor's INT1 pin to the GPIO below (active high, push-pull).

from lsm6ds3 import LSM6DS3
from machine import Pin
import time

INT_PIN = Pin(5, Pin.IN)

imu = LSM6DS3()
imu.enableAccelerator()
imu.enablePedometer()

previousTick = time.ticks_ms()

while True:
    if INT_PIN.value():
        status = imu.getEventStatus()
        if status["step"]:
            print("Step counter: {}".format(imu.getStepCounter()))

    # Print the step counter in any case every 3000 ms
    if time.ticks_diff(time.ticks_ms(), previousTick) >= 3000:
        print("Step counter: {}".format(imu.getStepCounter()))
        previousTick = time.ticks_ms()
