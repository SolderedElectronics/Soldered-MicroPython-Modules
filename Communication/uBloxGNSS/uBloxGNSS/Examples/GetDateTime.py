# FILE: GetDateTime.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read UTC date and time from a u-blox GNSS module
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
        if gnss.getDateValid() and gnss.getTimeValid():
            year = gnss.getYear()
            month = gnss.getMonth()
            day = gnss.getDay()
            hour = gnss.getHour()
            minute = gnss.getMinute()
            second = gnss.getSecond()
            nano = gnss.getNanosecond()
            print(
                f"{year:04d}-{month:02d}-{day:02d}  "
                f"{hour:02d}:{minute:02d}:{second:02d}.{nano // 1000000:03d} UTC"
            )
        else:
            print("Date/time not yet valid")
    else:
        print("Waiting for PVT...")

    time.sleep(1)
