# FILE: pcf85063a-basic.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Sets the time and reads the time each second.
# WORKS WITH: PCF85063A RTC Expander breakout: www.solde.red/333051
# LAST UPDATED: 2026-04-30

from pcf85063a import PCF85063A
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# rtc = PCF85063A(i2c)

# Init RTC
rtc = PCF85063A()

rtc.set_time(0, 0, 12, 4, 30, 4, 2026)

print("Time set!\n")

while True:
    t = rtc.get_time()

    year, month, day, weekday, hour, minute, second = t

    print(
        "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} (wd: {})".format(
            year, month, day, hour, minute, second, weekday
        )
    )

    time.sleep(1)
