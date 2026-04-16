# FILE: bhi385-gameRotationVector.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read a normalized quaternion from the Bosch BHI385 Smart IMU using the
#        Game Rotation Vector virtual sensor (sensor ID 37).
#        The Game Rotation Vector fuses accelerometer and gyroscope data to
#        produce a quaternion (x, y, z, w). It does NOT use a magnetometer, so
#        yaw is relative to the device orientation at power-on. Pitch and roll
#        are absolute (gravity-referenced).
# WORKS WITH: Bosch BHI385 Smart IMU breakout: www.solde.red/333232
# LAST UPDATED: 2026-04-15

from machine import Pin, I2C
from bhi385 import BHI385, BHI385_I2C_ADDR_HIGH
import time

SCL_PIN = 22
SDA_PIN = 21

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
imu = BHI385(i2c, BHI385_I2C_ADDR_HIGH)

print("BHI385 Game Rotation Vector example")

if not imu.begin():
    print("ERROR: BHI385 not found! Check wiring.")
    raise SystemExit

imu.enableDebug()

print("Loading firmware...")
with open("bhi385_firmware.bin", "rb") as f:
    firmware = f.read()

if not imu.loadFirmware(firmware):
    print("Firmware load failed.")
    raise SystemExit
print("Firmware loaded successfully.")

# Enable Game Rotation Vector at 100 Hz
if not imu.enableGameRotationVector(100.0):
    print("ERROR: Failed to enable Game Rotation Vector.")
    raise SystemExit
print("Game Rotation Vector enabled: 100 Hz")

imu.disableDebug()

print()
print("Quat X      Quat Y      Quat Z      Quat W")

while True:
    imu.update()

    if imu.quatUpdated():
        print(
            "{:.4f}      {:.4f}      {:.4f}      {:.4f}".format(
                imu.getQuatX(), imu.getQuatY(), imu.getQuatZ(), imu.getQuatW()
            )
        )

    imu.clearUpdatedFlags()
    time.sleep_ms(20)
