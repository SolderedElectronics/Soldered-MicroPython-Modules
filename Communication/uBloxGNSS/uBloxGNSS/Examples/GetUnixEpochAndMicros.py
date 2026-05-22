# FILE: GetUnixEpochAndMicros.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read Unix epoch time and sub-second microseconds from a u-blox GNSS module
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
        if gnss.getTimeFullyResolved():
            epoch, micros = gnss.getUnixEpoch()
            print(f"Unix epoch: {epoch}  Microseconds: {micros:06d}")
        else:
            print("Time not fully resolved yet")
    else:
        print("Waiting for PVT...")

    time.sleep(1)
