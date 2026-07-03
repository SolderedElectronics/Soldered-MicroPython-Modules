# FILE: lsm9ds1-accelerometerI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read acceleration from LSM9DS1 via I2C and print to console
# LAST UPDATED: 2026-06-02

from lsm9ds1 import LSM9DS1
import time

imu = LSM9DS1()

print("Accelerometer sample rate =", imu.accelerationSampleRate(), "Hz")
print("Acceleration in G's")
print("X\tY\tZ")

while True:
    if imu.accelAvailable():
        imu.readAccel()
        print(
            "{:.4f}\t{:.4f}\t{:.4f}".format(
                imu.calcAccel(imu.ax), imu.calcAccel(imu.ay), imu.calcAccel(imu.az)
            )
        )
    time.sleep_ms(10)
