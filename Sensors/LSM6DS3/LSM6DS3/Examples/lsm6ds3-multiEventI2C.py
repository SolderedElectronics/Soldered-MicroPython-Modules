# FILE: lsm6ds3-multiEventI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Enable all LSM6DS3 hardware events at once (INT1 + INT2)
# LAST UPDATED: 2026-07-02
#
# Wire the sensor's INT1 pin to INT1_PIN and INT2 pin to INT2_PIN below
# (both active high, push-pull).

from lsm6ds3 import LSM6DS3
from machine import Pin

INT1_PIN = Pin(5, Pin.IN)
INT2_PIN = Pin(4, Pin.IN)

imu = LSM6DS3()
imu.enableAccelerator()

imu.enablePedometer()
imu.enableTiltDetection()
imu.enableFreeFallDetection()
imu.enableSingleTapDetection()
imu.enableDoubleTapDetection()
imu.enable6dOrientation()
imu.enableWakeUpDetection()


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
    if INT1_PIN.value() or INT2_PIN.value():
        status = imu.getEventStatus()

        if status["step"]:
            print("Step counter: {}".format(imu.getStepCounter()))

        if status["freeFall"]:
            print("Free Fall Detected!")

        if status["tap"]:
            print("Single Tap Detected!")

        if status["doubleTap"]:
            print("Double Tap Detected!")

        if status["tilt"]:
            print("Tilt Detected!")

        if status["sixD"]:
            sendOrientation()

        if status["wakeUp"]:
            print("Wake up Detected!")
