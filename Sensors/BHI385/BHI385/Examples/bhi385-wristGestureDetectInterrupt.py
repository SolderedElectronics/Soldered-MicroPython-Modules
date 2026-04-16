# FILE: bhi385-wristGestureDetectInterrupt.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Detect wrist gestures using the BHI385 wrist gesture detect sensor
#        driven by a hardware interrupt for immediate response.
#        The wrist gesture sensor is a wake-up sensor — its events appear in
#        the wake-up FIFO and assert the INT pin. The ISR sets a flag and the
#        main loop calls update() immediately.
#        IMPORTANT: requires the "bsxsam_lite_Klio_cyclic" firmware variant
#        from Bosch Sensortec. The plain "bsxsam_lite" firmware does NOT expose
#        sensor ID 156.
# WORKS WITH: Bosch BHI385 Smart IMU breakout: www.solde.red/333232
# LAST UPDATED: 2026-04-15

from machine import Pin, I2C
from bhi385 import (BHI385, BHI385_I2C_ADDR_HIGH, BHI385_WRIST_LEFT,
                    BHI385_WRIST_GEST_NONE,
                    BHI385_WRIST_GEST_SHAKE_JIGGLE,
                    BHI385_WRIST_GEST_FLICK_IN,
                    BHI385_WRIST_GEST_FLICK_OUT)
import time

# GPIO connected to the BHI385 INT pin — change as needed
INT_PIN = 4


def gesture_name(gesture):
    if gesture == BHI385_WRIST_GEST_SHAKE_JIGGLE:
        return "Wrist shake/jiggle"
    elif gesture == BHI385_WRIST_GEST_FLICK_IN:
        return "Arm flick in"
    elif gesture == BHI385_WRIST_GEST_FLICK_OUT:
        return "Arm flick out"
    else:
        return "Unknown"


SCL_PIN = 22
SDA_PIN = 21

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
imu = BHI385(i2c, BHI385_I2C_ADDR_HIGH)

print("BHI385 Wrist Gesture Detect (interrupt mode)")

if not imu.begin():
    print("ERROR: BHI385 not found! Check wiring.")
    raise SystemExit

imu.enableDebug()

print("Loading firmware...")
with open("bhi385_firmware_klio.bin", "rb") as f:
    firmware = f.read()

if not imu.loadFirmware(firmware):
    print("Firmware load failed.")
    raise SystemExit
print("Firmware loaded successfully.")

# Enable wrist gesture detect. Pass BHI385_WRIST_RIGHT if the device is on
# the right wrist.
if not imu.enableWristGestureDetect(100.0, BHI385_WRIST_LEFT):
    print("ERROR: Failed to enable wrist gesture detect.")
    raise SystemExit
print("Wrist gesture detect enabled.")

imu.disableDebug()

# Attach interrupt AFTER firmware is loaded and sensors are configured
int_fired = False

def on_bhi385_int(pin):
    global int_fired
    int_fired = True

int_pin = Pin(INT_PIN, Pin.IN)
int_pin.irq(trigger=Pin.IRQ_RISING, handler=on_bhi385_int)

print()
print("Perform a wrist gesture to see it detected.")
print("  Wrist shake/jiggle : shake the wrist rapidly side to side")
print("  Arm flick in       : quick inward flick of the forearm")
print("  Arm flick out      : quick outward flick of the forearm")
print()
print("Gesture ID  Gesture Name")

while True:
    if not int_fired:
        continue

    int_fired = False
    imu.update()

    if imu.wristGestureUpdated():
        gesture = imu.getWristGesture()
        # Filter out "No Gesture" (value 0) — reported at startup and between gestures
        if gesture != BHI385_WRIST_GEST_NONE:
            print("{}           {}".format(gesture, gesture_name(gesture)))

    imu.clearUpdatedFlags()
