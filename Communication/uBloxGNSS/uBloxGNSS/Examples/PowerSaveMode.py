# FILE: PowerSaveMode.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Enable and disable continuous power-save (1 Hz cyclic tracking) on a u-blox GNSS module
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

print(f"Power save mode active: {gnss.getPowerSaveMode()}")

print("Enabling power save mode...")
gnss.powerSaveMode(True)
time.sleep_ms(100)
print(f"Power save mode active: {gnss.getPowerSaveMode()}")

time.sleep(5)

print("Disabling power save mode...")
gnss.powerSaveMode(False)
time.sleep_ms(100)
print(f"Power save mode active: {gnss.getPowerSaveMode()}")
