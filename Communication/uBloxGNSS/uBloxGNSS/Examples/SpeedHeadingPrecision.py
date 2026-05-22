# FILE: SpeedHeadingPrecision.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read ground speed, heading, and accuracy estimates from a u-blox GNSS module
# LAST UPDATED: 2026-05-22

from machine import I2C, Pin
import time
from gnss_ublox import SolderedGNSS

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
gnss = SolderedGNSS()

if not gnss.begin(i2c):
    print("u-blox GNSS not detected. Check wiring.")
    raise SystemExit

print("u-blox GNSS ready.\n")

while True:
    if gnss.getPVT():
        speed    = gnss.getGroundSpeed()       # mm/s
        heading  = gnss.getHeading()           # degrees * 1e-5
        sAcc     = gnss.getSpeedAccuracy()     # mm/s
        hAcc     = gnss.getHeadingAccuracy()   # degrees * 1e-5
        hPosAcc  = gnss.getHorizontalAccuracy()  # mm
        vPosAcc  = gnss.getVerticalAccuracy()    # mm
        pDOP     = gnss.getPDOP()              # * 0.01

        print(f"Speed: {speed / 1000:.3f} m/s (±{sAcc / 1000:.3f})  "
              f"Heading: {heading / 1e5:.5f}° (±{hAcc / 1e5:.5f})  "
              f"H-Acc: {hPosAcc / 1000:.3f} m  V-Acc: {vPosAcc / 1000:.3f} m  "
              f"pDOP: {pDOP * 0.01:.2f}")
    else:
        print("Waiting for PVT...")

    time.sleep(1)
