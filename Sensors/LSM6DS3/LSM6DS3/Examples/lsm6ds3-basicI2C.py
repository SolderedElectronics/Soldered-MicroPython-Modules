# FILE: lsm6ds3-basicI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read accelerometer and gyroscope data from the LSM6DS3 over I2C
# LAST UPDATED: 2026-07-02

from lsm6ds3 import LSM6DS3
import time

imu = LSM6DS3()
imu.enableAccelerator()
imu.enableGyro()

while True:
    time.sleep_ms(250)

    ax, ay, az = imu.getAcceleratorAxes()
    gx, gy, gz = imu.getGyroAxes()

    print("| Acc[mg]: {} {} {} | Gyr[mdps]: {} {} {} |".format(ax, ay, az, gx, gy, gz))
