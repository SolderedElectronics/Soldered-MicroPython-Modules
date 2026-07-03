# FILE: GetProtocolVersion.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read the UBX protocol version from a u-blox GNSS module
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

high = gnss.getProtocolVersionHigh()
low = gnss.getProtocolVersionLow()

if high is not None:
    print(f"Protocol version: {high}.{low:02d}")
else:
    print("Could not retrieve protocol version.")
