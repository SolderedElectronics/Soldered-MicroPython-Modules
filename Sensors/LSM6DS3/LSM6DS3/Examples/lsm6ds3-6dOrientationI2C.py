# FILE: lsm6ds3-6dOrientationI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Use LSM6DS3 6D orientation detection via hardware interrupt (INT1)
# LAST UPDATED: 2026-07-02
#
# Wire the sensor's INT1 pin to the GPIO below (active high, push-pull).

from lsm6ds3 import LSM6DS3
from machine import Pin

INT_PIN = Pin(5, Pin.IN)

imu = LSM6DS3()
imu.enableAccelerator()
imu.enable6dOrientation()


def sendOrientation():
    xl = imu.get6dOrientationXl()
    xh = imu.get6dOrientationXh()
    yl = imu.get6dOrientationYl()
    yh = imu.get6dOrientationYh()
    zl = imu.get6dOrientationZl()
    zh = imu.get6dOrientationZh()

    if not xl and not yl and not zl and not xh and yh and not zh:
        print("Orientation: Top")
    elif xl and not yl and not zl and not xh and not yh and not zh:
        print("Orientation: Right")
    elif not xl and not yl and not zl and xh and not yh and not zh:
        print("Orientation: Bottom")
    elif not xl and yl and not zl and not xh and not yh and not zh:
        print("Orientation: Left")
    elif not xl and not yl and not zl and not xh and not yh and zh:
        print("Orientation: Face Up")
    elif not xl and not yl and zl and not xh and not yh and not zh:
        print("Orientation: Face Down")
    else:
        print("None of the 6D orientation axes is set")


while True:
    if INT_PIN.value():
        status = imu.getEventStatus()
        if status["sixD"]:
            sendOrientation()
