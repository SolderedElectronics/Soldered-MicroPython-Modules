# FILE: FixType.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read and display the current GNSS fix type
# LAST UPDATED: 2026-05-22

from machine import I2C, Pin
import time
from gnss_ublox import SolderedGNSS

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
gnss = SolderedGNSS()

if not gnss.begin(i2c):
    print("u-blox GNSS not detected. Check wiring.")
    raise SystemExit

FIX_NAMES = {
    0: "No fix",
    1: "Dead reckoning",
    2: "2D fix",
    3: "3D fix",
    4: "GNSS + dead reckoning",
    5: "Time only",
}

print("u-blox GNSS ready.\n")

while True:
    if gnss.getPVT():
        fix = gnss.getFixType()
        siv = gnss.getSIV()
        label = FIX_NAMES.get(fix, f"Unknown ({fix})")
        print(f"Fix type: {fix} ({label})  Satellites in view: {siv}")
    else:
        print("Waiting for PVT...")

    time.sleep(1)
