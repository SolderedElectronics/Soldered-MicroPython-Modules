# FILE: bhi385-doubleTapInterrupt.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Detect double taps using the BHI385 multi-tap sensor driven by a
#        hardware interrupt for immediate response. The tap sensor is a wake-up
#        sensor — its events appear in the wake-up FIFO and assert the INT pin.
#        Note: double-tap detection requires the firmware to observe two impulses
#        within a short window, so the interrupt fires slightly later than for a
#        single tap — this is expected behaviour.
# WORKS WITH: Bosch BHI385 Smart IMU breakout: www.solde.red/333232
# LAST UPDATED: 2026-04-15

from machine import Pin, I2C
from bhi385 import BHI385, BHI385_I2C_ADDR_HIGH, BHI385_TAP_DOUBLE
import time

# GPIO connected to the BHI385 INT pin — change as needed
INT_PIN = 4

SCL_PIN = 22
SDA_PIN = 21

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
imu = BHI385(i2c, BHI385_I2C_ADDR_HIGH)

print("BHI385 Double Tap (interrupt mode)")

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

if not imu.enableMultiTapDetect(BHI385_TAP_DOUBLE, 100.0):
    print("ERROR: Failed to enable multi-tap sensor.")
    raise SystemExit
print("Double tap detection enabled.")

imu.disableDebug()

# Attach interrupt AFTER firmware is loaded and sensors are configured
int_fired = False


def on_bhi385_int(pin):
    global int_fired
    int_fired = True


int_pin = Pin(INT_PIN, Pin.IN)
int_pin.irq(trigger=Pin.IRQ_RISING, handler=on_bhi385_int)

print()
print("Tap the sensor twice quickly to trigger a double tap.")
print("Count  Type")

tap_count = 0

while True:
    if not int_fired:
        continue

    int_fired = False
    imu.update()

    if imu.tapUpdated() and imu.getTapType() == BHI385_TAP_DOUBLE:
        tap_count += 1
        print("{}      Double tap".format(tap_count))

    imu.clearUpdatedFlags()
