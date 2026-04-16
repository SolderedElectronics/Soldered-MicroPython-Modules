# FILE: bhi385-readAccelGyro.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read accelerometer and gyroscope data from the Bosch BHI385 Smart IMU
# WORKS WITH: Bosch BHI385 Smart IMU breakout: www.solde.red/333232
# LAST UPDATED: 2026-04-15

from machine import Pin, I2C
from bhi385 import BHI385, BHI385_I2C_ADDR_HIGH, BHI385_ACCEL_8G, BHI385_GYRO_2000DPS
import time

# Initialize I2C at 400 kHz for faster firmware upload (~1.3 s vs ~5 s)
SCL_PIN = 22
SDA_PIN = 21

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)

# Initialize sensor. Use BHI385_I2C_ADDR_HIGH (0x29) if HSDO is tied to VDDIO.
imu = BHI385(i2c, BHI385_I2C_ADDR_HIGH)

print("BHI385 Accelerometer and Gyroscope example")

if not imu.begin():
    print("ERROR: BHI385 not found! Check wiring, I2C address,.")
    print("       Chip ID read: 0x{:02X}".format(imu.getChipId()))
    print("       Expected:   0x7C")
    raise SystemExit

print("BHI385 found. Boot status: 0x{:02X}".format(imu.getBootStatus()))

# Enable verbose debug output so every step of firmware loading is printed
imu.enableDebug()

# Load firmware from a binary file. Obtain the firmware from Bosch Sensortec
# and place it on the filesystem as "bhi385_firmware.bin".
print("Loading firmware...")
with open("bhi385_firmware.bin", "rb") as f:
    firmware = f.read()

if not imu.loadFirmware(firmware):
    print("Firmware load failed.")
    raise SystemExit

print("Firmware loaded successfully.")

# Enable accelerometer: 100 Hz, +-8 g
if not imu.enableAccelerometer(100.0, BHI385_ACCEL_8G):
    print("ERROR: Failed to enable accelerometer.")
    raise SystemExit
print("Accelerometer enabled: 100 Hz, +-8 g")

# Enable gyroscope: 100 Hz, +-2000 deg/s
if not imu.enableGyroscope(100.0, BHI385_GYRO_2000DPS):
    print("ERROR: Failed to enable gyroscope.")
    raise SystemExit
print("Gyroscope enabled: 100 Hz, +-2000 deg/s")

imu.disableDebug()

print()
print("AccelX(g)  AccelY(g)  AccelZ(g)  GyroX(dps)  GyroY(dps)  GyroZ(dps)")

# Main loop — poll at ~50 Hz. At 100 Hz sensor rate this typically returns
# 2 samples per call.
while True:
    imu.update()

    accel_str = ""
    if imu.accelUpdated():
        accel_str = "{:.4f}  {:.4f}  {:.4f}".format(
            imu.getAccelX(), imu.getAccelY(), imu.getAccelZ()
        )
    else:
        accel_str = "N/A        N/A        N/A"

    gyro_str = ""
    if imu.gyroUpdated():
        gyro_str = "{:.4f}  {:.4f}  {:.4f}".format(
            imu.getGyroX(), imu.getGyroY(), imu.getGyroZ()
        )
    else:
        gyro_str = "N/A         N/A         N/A"

    print("{}  {}".format(accel_str, gyro_str))

    imu.clearUpdatedFlags()
    time.sleep_ms(20)
