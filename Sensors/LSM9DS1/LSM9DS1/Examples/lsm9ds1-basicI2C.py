# FILE: lsm9ds1-basicI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read all axes from LSM9DS1 via I2C, print values and calculated attitude/heading
# LAST UPDATED: 2026-06-02

from lsm9ds1 import LSM9DS1
import time
import math

# Magnetic declination for your location (degrees).
# Find yours at: http://www.ngdc.noaa.gov/geomag-web/#declination
DECLINATION = 5.37  # Osijek, Croatia

PRINT_SPEED_MS = 250

imu = LSM9DS1()

lastPrint = time.ticks_ms()


def printGyro():
    print(
        "G: {:.2f}, {:.2f}, {:.2f} deg/s".format(
            imu.calcGyro(imu.gx), imu.calcGyro(imu.gy), imu.calcGyro(imu.gz)
        )
    )


def printAccel():
    print(
        "A: {:.2f}, {:.2f}, {:.2f} g".format(
            imu.calcAccel(imu.ax), imu.calcAccel(imu.ay), imu.calcAccel(imu.az)
        )
    )


def printMag():
    print(
        "M: {:.2f}, {:.2f}, {:.2f} gauss".format(
            imu.calcMag(imu.mx), imu.calcMag(imu.my), imu.calcMag(imu.mz)
        )
    )


def printAttitude(ax, ay, az, mx, my, mz):
    roll = math.atan2(ay, az)
    pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))

    if my == 0:
        heading = math.pi if mx < 0 else 0.0
    else:
        heading = math.atan2(mx, my)

    heading -= DECLINATION * math.pi / 180.0
    if heading > math.pi:
        heading -= 2 * math.pi
    elif heading < -math.pi:
        heading += 2 * math.pi

    print(
        "Pitch, Roll: {:.2f}, {:.2f}".format(
            pitch * 180.0 / math.pi, roll * 180.0 / math.pi
        )
    )
    print("Heading: {:.2f}".format(heading * 180.0 / math.pi))


while True:
    if imu.gyroAvailable():
        imu.readGyro()
    if imu.accelAvailable():
        imu.readAccel()
    if imu.magAvailable():
        imu.readMag()

    if time.ticks_diff(time.ticks_ms(), lastPrint) >= PRINT_SPEED_MS:
        printGyro()
        printAccel()
        printMag()
        # Mag x and y are swapped relative to accel (matches Arduino library behavior)
        printAttitude(
            imu.calcAccel(imu.ax),
            imu.calcAccel(imu.ay),
            imu.calcAccel(imu.az),
            -imu.calcMag(imu.my),
            -imu.calcMag(imu.mx),
            imu.calcMag(imu.mz),
        )
        print()
        lastPrint = time.ticks_ms()
