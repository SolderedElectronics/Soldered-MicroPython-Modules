# FILE: lsm9ds1-magnetometerI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read magnetic field from LSM9DS1 via I2C and print to console
# LAST UPDATED: 2026-06-02

from lsm9ds1 import LSM9DS1
import time

imu = LSM9DS1()

print("Magnetic field sample rate =", imu.magneticFieldSampleRate(), "Hz")
print("Magnetic Field in Gauss")
print("X\tY\tZ")

while True:
    if imu.magAvailable():
        imu.readMag()
        print(
            "{:.4f}\t{:.4f}\t{:.4f}".format(
                imu.calcMag(imu.mx), imu.calcMag(imu.my), imu.calcMag(imu.mz)
            )
        )
    time.sleep_ms(10)
