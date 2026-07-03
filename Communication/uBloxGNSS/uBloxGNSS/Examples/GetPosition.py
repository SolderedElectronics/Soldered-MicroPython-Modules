# FILE: GetPosition.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read latitude, longitude, altitude, and fix info from a u-blox GNSS module
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
        lat = gnss.getLatitude()
        lon = gnss.getLongitude()
        alt = gnss.getAltitude()
        siv = gnss.getSIV()
        fix = gnss.getFixType()

        print(
            f"Lat: {lat / 1e7:.7f}  Lon: {lon / 1e7:.7f}  Alt: {alt / 1000:.3f} m  "
            f"Fix: {fix}  Satellites: {siv}"
        )
    else:
        print("Waiting for valid PVT data...")

    time.sleep(1)
