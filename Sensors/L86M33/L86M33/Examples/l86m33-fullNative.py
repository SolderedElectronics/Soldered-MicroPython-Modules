# FILE: l86m33-fullNative.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Full native UART example for the L86-M33 GNSS breakout - shows all decoded fields plus distance/course to a fixed city
# LAST UPDATED: 2026-07-02

from l86m33 import GNSS
import time

# Adjust to your board's wiring and a free hardware UART peripheral
UART_ID = 1
TX_PIN = 17
RX_PIN = 16

gps = GNSS(UART_ID, TX_PIN, RX_PIN)

# Calculate the distance/course between the current GNSS location and Osijek, Croatia
CITY_LAT = 45.5550
CITY_LON = 18.6955

start_time = time.ticks_ms()


def smart_delay(ms):
    """Feed the parser with any pending UART bytes while waiting, instead of a plain sleep."""
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < ms:
        while gps.uart.any():
            b = gps.uart.read(1)
            if b:
                gps.encode(b[0])


print("Sats HDOP  Latitude    Longitude    Age  Date       Time     Alt     Course Speed Card Dist(km) Course Card  Chars Sentences Checksum")

while True:
    print("{:>4} ".format(gps.satellites.value() if gps.satellites.isValid() else "****"), end="")
    print("{:>5.1f} ".format(gps.hdop.hdop()) if gps.hdop.isValid() else "***** ", end="")

    if gps.location.isValid():
        print("{:>10.6f}  {:>10.6f} ".format(gps.location.lat(), gps.location.lng()), end="")
        print("{:>4} ".format(gps.location.age()), end="")
    else:
        print("*INVALID*   *INVALID*  **** ", end="")

    if gps.date.isValid() and gps.time.isValid():
        print("{:02d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d} ".format(
            gps.date.month(), gps.date.day(), gps.date.year(),
            gps.time.hour(), gps.time.minute(), gps.time.second()), end="")
    else:
        print("**INVALID** ******** ", end="")

    print("{:>7.2f} ".format(gps.altitude.meters()) if gps.altitude.isValid() else "******* ", end="")
    print("{:>6.2f} ".format(gps.course.deg()) if gps.course.isValid() else "****** ", end="")
    print("{:>5.2f} ".format(gps.speed.kmph()) if gps.speed.isValid() else "***** ", end="")
    print("{:<4} ".format(GNSS.cardinal(gps.course.deg())) if gps.course.isValid() else "***  ", end="")

    if gps.location.isValid():
        distance_km = GNSS.distanceBetween(gps.location.lat(), gps.location.lng(), CITY_LAT, CITY_LON) / 1000
        course_to_city = GNSS.courseTo(gps.location.lat(), gps.location.lng(), CITY_LAT, CITY_LON)
        print("{:>8.0f} {:>6.2f} {:<4} ".format(distance_km, course_to_city, GNSS.cardinal(course_to_city)), end="")
    else:
        print("****     ****   ***  ", end="")

    print("{:>5} {:>9} {:>8}".format(gps.charsProcessed(), gps.sentencesWithFix(), gps.failedChecksum()))

    # Use smart_delay() instead of a plain sleep, otherwise incoming GNSS data gets lost
    smart_delay(1000)

    # No data in the first 5 seconds from startup? Something is wrong, check wiring!
    if time.ticks_diff(time.ticks_ms(), start_time) > 5000 and gps.charsProcessed() < 10:
        print("No GPS data received: check wiring")
