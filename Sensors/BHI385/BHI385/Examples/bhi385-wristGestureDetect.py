# FILE: bhi385-wristGestureDetect.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Detect wrist gestures using the Bosch BHI385 Smart IMU wrist gesture
#        detect virtual sensor (sensor ID 156).
#        IMPORTANT: this sensor requires the "bsxsam_lite_Klio_cyclic" firmware
#        variant from Bosch Sensortec. The plain "bsxsam_lite" firmware does NOT
#        expose sensor ID 156.
# WORKS WITH: Bosch BHI385 Smart IMU breakout: www.solde.red/333232
# LAST UPDATED: 2026-04-15

from machine import Pin, I2C
from bhi385 import (
    BHI385,
    BHI385_I2C_ADDR_HIGH,
    BHI385_WRIST_LEFT,
    BHI385_WRIST_GEST_SHAKE_JIGGLE,
    BHI385_WRIST_GEST_FLICK_IN,
    BHI385_WRIST_GEST_FLICK_OUT,
)
import time


def gesture_name(gesture):
    if gesture == BHI385_WRIST_GEST_SHAKE_JIGGLE:
        return "Wrist shake/jiggle"
    elif gesture == BHI385_WRIST_GEST_FLICK_IN:
        return "Arm flick in"
    elif gesture == BHI385_WRIST_GEST_FLICK_OUT:
        return "Arm flick out"
    else:
        return "No gesture"


SCL_PIN = 22
SDA_PIN = 21

i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
imu = BHI385(i2c, BHI385_I2C_ADDR_HIGH)

print("BHI385 Wrist Gesture Detect example")

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

print()
print("Perform a wrist gesture to see it detected.")
print("  Wrist shake/jiggle : shake the wrist rapidly side to side")
print("  Arm flick in       : quick inward flick of the forearm")
print("  Arm flick out      : quick outward flick of the forearm")
print()
print("Gesture ID  Gesture Name")

while True:
    imu.update()

    if imu.wristGestureUpdated():
        gesture = imu.getWristGesture()
        print("{}           {}".format(gesture, gesture_name(gesture)))

    imu.clearUpdatedFlags()
