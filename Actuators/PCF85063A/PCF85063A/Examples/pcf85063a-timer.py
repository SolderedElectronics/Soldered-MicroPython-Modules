# FILE: pcf85063a-timer.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Sets the time and timer for 5 seconds.
# WORKS WITH: PCF85063A RTC Expander breakout: www.solde.red/333051
# LAST UPDATED: 2026-04-30

from pcf85063a import PCF85063A, PCF85063A_TIMER_CLOCK_1HZ
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# rtc = PCF85063A(i2c)

# Init RTC
rtc = PCF85063A()

countdown_time = 5  # seconds

print("Now is:")
rtc.set_time(0, 54, 6, 6, 16, 5, 2020)


def print_current_time():
    year, month, day, weekday, hour, minute, second = rtc.get_time()

    weekdays = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]

    print(
        "{} , {:02d}.{:02d}.{:04d} {:02d}:{:02d}:{:02d}".format(
            weekdays[weekday], day, month, year, hour, minute, second
        )
    )


while True:
    print_current_time()

    print("Setting timer countdown, waking up in", countdown_time, "seconds.")

    rtc.set_timer(
        PCF85063A_TIMER_CLOCK_1HZ, countdown_time, int_enable=False, int_pulse=False
    )

    print("Waiting for a countdown")

    while not rtc.get_timer_flag():
        print(".", end="")
        time.sleep(1)

    print("\nInterrupt triggered on:")
