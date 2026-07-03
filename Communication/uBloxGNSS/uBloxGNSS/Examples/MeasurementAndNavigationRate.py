# FILE: MeasurementAndNavigationRate.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read and set measurement and navigation rates on a u-blox GNSS module
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

measRate = gnss.getMeasurementRate()
navRate = gnss.getNavigationRate()
print(f"Current measurement rate: {measRate} ms  Navigation rate: {navRate} cycles")

# Set 5 Hz (200 ms measurement period, 1 nav solution per measurement)
gnss.setNavigationFrequency(5)
time.sleep_ms(100)

measRate = gnss.getMeasurementRate()
navRate = gnss.getNavigationRate()
navFreq = gnss.getNavigationFrequency()
print(
    f"Updated measurement rate : {measRate} ms  Navigation rate: {navRate} cycles  "
    f"Nav frequency: {navFreq} Hz"
)
