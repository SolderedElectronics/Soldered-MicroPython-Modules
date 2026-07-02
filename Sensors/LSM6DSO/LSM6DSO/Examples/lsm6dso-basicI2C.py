# FILE: lsm6dso-basicI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read accelerometer and gyroscope data from the LSM6DSO over I2C
# LAST UPDATED: 2026-07-02

from lsm6dso import LSM6DSO, VARIANT_LSM6DSO32
import time

imu = LSM6DSO()

if imu.getVariant() == VARIANT_LSM6DSO32:
    print("LSM6DSO32 detected - can use 32g range")
    imu.setAcceleratorFullScale(32)
else:
    print("LSM6DSO detected - max 16g range")
    imu.setAcceleratorFullScale(16)

imu.enableAccelerator()
imu.enableGyro()

while True:
    time.sleep_ms(250)

    ax, ay, az = imu.getAcceleratorAxes()
    gx, gy, gz = imu.getGyroAxes()

    print("| Acc[mg]: {} {} {} | Gyr[mdps]: {} {} {} |".format(ax, ay, az, gx, gy, gz))
