# FILE: GetLeapSecondInfo.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read leap second event information from a u-blox GNSS module
# LAST UPDATED: 2026-05-22

from machine import I2C, Pin
from gnss_ublox import (
    SolderedGNSS,
    LS_SRC_GPS,
    LS_SRC_GLONASS,
    LS_SRC_BEIDOU,
    LS_SRC_GALILEO,
)

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
gnss = SolderedGNSS()

if not gnss.begin(i2c):
    print("u-blox GNSS not detected. Check wiring.")
    raise SystemExit

print("u-blox GNSS ready.\n")

SOURCE_NAMES = {
    0: "Default (firmware)",
    1: "GLONASS",
    2: "GPS",
    3: "SBAS",
    4: "BeiDou",
    5: "Galileo",
    6: "Aided",
    7: "Configured",
    255: "Unknown",
}

if gnss.getLeapSecondEvent():
    li, timeToEvent = gnss.getLeapIndicator()
    currLs, src = gnss.getCurrentLeapSeconds()

    print(f"Current leap seconds : {currLs}  (source: {SOURCE_NAMES.get(src, src)})")
    print(f"Leap indicator       : {li}  Time to next event: {timeToEvent} s")
else:
    print("Could not retrieve leap second information.")
