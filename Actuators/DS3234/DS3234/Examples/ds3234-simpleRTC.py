# FILE: DS3234-simpleRTC.py
# AUTHOR: Soldered
# BRIEF: Example showing how to Initialize the DS3234 RTC
#        and set the time and alarms
# WORKS WITH: DS3234 RTC Breakout: www.solde.red/333358
# LAST UPDATED: 2025-09-15

import machine
import time
from ds3234 import DS3234

# Configurable Pin Definitions for ESP32
DS3234_CS_PIN = 5  # DS3234 RTC Chip-select pin

# ESP32 SPI pin assignments (change these based on your wiring)
# Default ESP32 SPI pins:
# HSPI: SCLK=14, MOSI=13, MISO=12
# VSPI: SCLK=18, MOSI=23, MISO=19

# Using HSPI
spi = machine.SPI(
    1,
    baudrate=1000000,
    polarity=1,
    phase=1,
    sck=machine.Pin(18),
    mosi=machine.Pin(23),
    miso=machine.Pin(19),
)
cs_pin = machine.Pin(DS3234_CS_PIN, machine.Pin.OUT)

# Create an instance of the RTC object
rtc = DS3234(spi, cs_pin)

# Create an instance of the RTC object
# If using the SQW pin as an interrupt (uncomment if needed)
# interrupt_pin = machine.Pin(INTERRUPT_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

# Use the serial monitor to view time/date output
print("Initializing DS3234 RTC...")

# Initialize the RTC
# (The __init__ method already handles initialization in the class)

# Set to 12-hour mode if desired (uncomment)
# rtc.set12Hour()

# Now set the time...
# You can use the autoTime() function to set the RTC's clock and
# date to the system's current time
rtc.autoTime()

# Or you can use the rtc.setTime(s, m, h, day, date, month, year)
# function to explicitly set the time:
# e.g. 7:32:16 | Monday October 31, 2016:
# rtc.setTime(16, 32, 7, 2, 31, 10, 16)  # Uncomment to manually set time

# Update time/date values, so we can set alarms
rtc.update()

# Configure Alarm(s):
# (Optional: enable SQW pin as an interrupt)
rtc.enableAlarmInterrupt()

# Set alarm1 to alert when seconds hits 30
rtc.setAlarm1(30)

# Set alarm2 to alert when minute increments by 1
rtc.setAlarm2(rtc.minute() + 1)

print("RTC initialized and alarms set")


def print_time():
    # Print hour
    print(str(rtc.hour()) + ":", end="")

    # Print minute with leading zero if needed
    if rtc.minute() < 10:
        print("0", end="")
    print(str(rtc.minute()) + ":", end="")

    # Print second with leading zero if needed
    if rtc.second() < 10:
        print("0", end="")
    print(str(rtc.second()), end="")

    # If we're in 12-hour mode
    if rtc.is12hour():
        # Use rtc.pm() to read the AM/PM state of the hour
        if rtc.pm():
            print(" PM", end="")  # Returns true if PM
        else:
            print(" AM", end="")

    print(" | ", end="")

    # Few options for printing the day, pick one:
    print(rtc.dayStr(), end="")  # Print day string
    # print(rtc.dayChar(), end="")  # Print day character
    # print(rtc.day(), end="")  # Print day integer (1-7, Sun-Sat)

    print(" - ", end="")

    # Print date in USA format (MM/DD/YYYY) or international (DD/MM/YYYY)
    PRINT_USA_DATE = True  # Change to False for international format

    if PRINT_USA_DATE:
        print(
            str(rtc.month()) + "/" + str(rtc.date()) + "/", end=""
        )  # Print month/date
    else:
        print(
            str(rtc.date()) + "/" + str(rtc.month()) + "/", end=""
        )  # Print date/month

    print(str(rtc.year()))  # Print year


last_second = -1

while True:
    rtc.update()

    if rtc.second() != last_second:  # If the second has changed
        print_time()  # Print the new time
        last_second = rtc.second()  # Update last_second value

    # Check for alarm interrupts
    # If using interrupt pin (uncomment if needed):
    # if interrupt_pin.value() == 0:  # Interrupt pin is active-low
    # Check rtc.alarm1() to see if alarm 1 triggered the interrupt

    if rtc.alarm1(clear=True) == True:  # Clear the alarm flag
        print("ALARM 1!")
        # Re-set the alarm for when s=30:
        rtc.setAlarm1(30)

    # Check rtc.alarm2() to see if alarm 2 triggered the interrupt
    if rtc.alarm2(clear=True) == True:  # Clear the alarm flag
        print("ALARM 2!")
        # Re-set the alarm for when m increments by 1
        rtc.setAlarm2(rtc.minute() + 1)

    time.sleep(0.1)  # Small delay to prevent busy waiting
