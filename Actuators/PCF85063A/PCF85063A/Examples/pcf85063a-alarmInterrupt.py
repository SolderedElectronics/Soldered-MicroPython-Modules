# FILE: pcf85063a-alarmInterrupt.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Sets the time and alarm and goes to sleep. Wakes up on RTC interrupt.
#        File must be saved as main.py on MicroPython device.
# WORKS WITH: PCF85063A RTC Expander breakout: www.solde.red/333051
# LAST UPDATED: 2026-04-30

from machine import I2C, Pin, deepsleep
import time
import machine
import esp32
from pcf85063a import PCF85063A

# Set up wake up pin
wake_pin = Pin(2, Pin.IN, Pin.PULL_UP)
esp32.wake_on_ext0(pin=wake_pin, level=esp32.WAKEUP_ALL_LOW)

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# rtc = PCF85063A(i2c)

# Init RTC
rtc = PCF85063A()


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


def check_alarm():
    alarm_day, alarm_weekday, alarm_hour, alarm_minute, alarm_second = rtc.get_alarm()
    weekdays = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]
    print("Alarm is set to match:")
    if alarm_weekday != 99:
        print(weekdays[alarm_weekday], end=", ")
    if alarm_day != 99:
        print("Date:", alarm_day, end=" ")
    if alarm_hour != 99:
        print("hour:", alarm_hour, end=" ")
    if alarm_minute != 99:
        print("minute:", alarm_minute, end=" ")
    if alarm_second != 99:
        print("second:", alarm_second, end=" ")
    print()


if machine.reset_cause() == machine.DEEPSLEEP_RESET:
    print("Woke from deep sleep — skipping RTC init")
    rtc.clear_alarm()
else:
    print("Fresh boot — setting time and alarm")
    rtc.set_time(0, 54, 6, 6, 16, 5, 2020)
    rtc.set_alarm(30, 54, 99, 99, 99)
    check_alarm()


while True:
    print_current_time()
    print("Entering sleep mode in 1 second")
    time.sleep(1)
    print("Going to deep sleep...")
    time.sleep_ms(100)
    deepsleep()
