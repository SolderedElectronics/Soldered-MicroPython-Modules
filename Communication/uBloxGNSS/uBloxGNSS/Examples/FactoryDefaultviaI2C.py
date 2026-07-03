# FILE: FactoryDefaultviaI2C.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Reset a u-blox GNSS module to factory defaults over I2C
# LAST UPDATED: 2026-05-22

from machine import I2C, Pin
import time
from gnss_ublox import SolderedGNSS

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
gnss = SolderedGNSS()

if not gnss.begin(i2c):
    print("u-blox GNSS not detected. Check wiring.")
    raise SystemExit

print("u-blox GNSS ready.")
print("Sending factory reset command...")

gnss.factoryReset()

# Module resets and re-initialises — wait before reconnecting
print("Waiting for module to restart...")
time.sleep(3)

if gnss.begin(i2c):
    print("Module successfully reset to factory defaults and is ready.")
else:
    print("Could not reconnect after factory reset.")
