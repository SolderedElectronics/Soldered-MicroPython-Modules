# FILE: PowerOff.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Put the u-blox GNSS module into backup mode for a set duration
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
print("Powering off for 10 seconds...")

# Power off for 10 000 ms; the module wakes up automatically after the duration
gnss.powerOff(10000)

print("Power-off command sent. Waiting for module to wake up...")
time.sleep(12)

# Re-initialise after wake-up
if gnss.begin(i2c):
    print("Module woke up and is ready again.")
else:
    print("Could not communicate with module after wake-up.")
