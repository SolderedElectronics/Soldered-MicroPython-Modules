# FILE: bhi385-readAccelGyroInterrupt.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read accelerometer and gyroscope data from the Bosch BHI385 Smart IMU
#        using a hardware interrupt for lowest-latency FIFO draining.
#        The BHI385 INT pin is pulled HIGH whenever new data is waiting in the
#        non-wake-up FIFO. A hardware interrupt on the host MCU detects this
#        rising edge and sets a flag; the main loop then calls update()
#        immediately instead of polling on a fixed timer.
# WORKS WITH: Bosch BHI385 Smart IMU breakout: www.solde.red/333232
# LAST UPDATED: 2026-04-15

from machine import Pin, I2C
from bhi385 import BHI385, BHI385_I2C_ADDR_HIGH
import time

# GPIO connected to the BHI385 INT pin — change as needed
INT_PIN = 4

SCL_PIN = 22
SDA_PIN = 21

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
imu = BHI385(i2c, BHI385_I2C_ADDR_HIGH)

print("BHI385 Accel and Gyro (interrupt mode)")

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

if not imu.enableAccelerometer(100.0):
    print("ERROR: Failed to enable accelerometer.")
    raise SystemExit

if not imu.enableGyroscope(100.0):
    print("ERROR: Failed to enable gyroscope.")
    raise SystemExit

imu.disableDebug()

# Attach interrupt AFTER firmware is loaded and sensors are configured so that
# the initial boot interrupt does not trigger the handler early.
int_fired = False

def on_bhi385_int(pin):
    global int_fired
    int_fired = True

int_pin = Pin(INT_PIN, Pin.IN)
int_pin.irq(trigger=Pin.IRQ_RISING, handler=on_bhi385_int)

print("Sensors enabled at 100 Hz. Waiting for data...")
print()
print("Accel X (g)  Accel Y (g)  Accel Z (g)  Gyro X (dps)  Gyro Y (dps)  Gyro Z (dps)")

while True:
    if not int_fired:
        continue

    int_fired = False
    imu.update()

    printed = False

    if imu.accelUpdated():
        print("{:.3f}  {:.3f}  {:.3f}".format(
            imu.getAccelX(), imu.getAccelY(), imu.getAccelZ()), end="")
        printed = True

    if imu.gyroUpdated():
        if not printed:
            # Pad accel columns if accel was not in this packet
            print("N/A          N/A          N/A", end="")
        print("  {:.3f}  {:.3f}  {:.3f}".format(
            imu.getGyroX(), imu.getGyroY(), imu.getGyroZ()))
        printed = True
    elif printed:
        print()

    imu.clearUpdatedFlags()
