# FILE: AltitudeMSL.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read altitude above mean sea level from a u-blox GNSS module
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
        alt_ellipsoid = gnss.getAltitude()
        alt_msl = gnss.getAltitudeMSL()
        print(
            f"Altitude (ellipsoid): {alt_ellipsoid / 1000:.3f} m  "
            f"Altitude (MSL): {alt_msl / 1000:.3f} m"
        )
    else:
        print("Waiting for valid PVT data...")

    time.sleep(1)
