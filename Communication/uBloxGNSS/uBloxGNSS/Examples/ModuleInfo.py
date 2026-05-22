# FILE: ModuleInfo.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read software version, hardware version and extension strings from a u-blox GNSS module
# LAST UPDATED: 2026-05-22

from machine import I2C, Pin
from gnss_ublox import SolderedGNSS

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
gnss = SolderedGNSS()

if not gnss.begin(i2c):
    print("u-blox GNSS not detected. Check wiring.")
    raise SystemExit

print("u-blox GNSS ready.\n")

info = gnss.getModuleInfo()
if info:
    print(f"SW version : {info.get('swVersion', 'N/A')}")
    print(f"HW version : {info.get('hwVersion', 'N/A')}")
    for i, ext in enumerate(info.get('extensions', [])):
        print(f"Extension {i}: {ext}")
else:
    print("Could not retrieve module info.")
