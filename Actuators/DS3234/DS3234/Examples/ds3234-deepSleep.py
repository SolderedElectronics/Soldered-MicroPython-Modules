# FILE: DS3234-simpleRTC.py
# AUTHOR: Soldered
# BRIEF: Example showing how to wake up from deep sleep
#        Using the INT pin on the breakout board
# WORKS WITH: DS3234 RTC Breakout: www.solde.red/333358
# LAST UPDATED: 2025-09-15

import machine
import time
import esp32
from DS3234 import DS3234

# Define CS pin for DS3234
RTC_CS_PIN = 5

# Define wake-up pin (must be RTC-capable GPIO)
# ESP32 RTC-capable pins: 0, 2, 4, 12-15, 25-27, 32-39
WAKEUP_PIN = 26  # Must be RTC-capable pin

# Initialize SPI and CS pin for DS3234
# Using VSPI (SPI ID 2) with default ESP32 pins
spi = machine.SPI(
    2,
    baudrate=1000000,
    polarity=1,
    phase=1,
    sck=machine.Pin(18),
    mosi=machine.Pin(23),
    miso=machine.Pin(19),
)
cs_pin = machine.Pin(RTC_CS_PIN, machine.Pin.OUT)

# Create an instance of the RTC object
rtc = DS3234(spi, cs_pin)

print("Initializing DS3234 RTC...")

# Check if this is a wake-up from deep sleep
wake_reason = machine.wake_reason()

if wake_reason == machine.PIN_WAKE:
    print("Woke up from deep sleep (RTC alarm)!")

    # Read and display current time
    rtc.update()

    print(
        "Current time: {0}:{1:02d}:{2:02d}".format(
            rtc.hour(), rtc.minute(), rtc.second()
        )
    )

    print("Date: {0}/{1}/{2}".format(rtc.month(), rtc.date(), rtc.year() + 2000))

    # Clear alarm flags
    if rtc.alarm1(clear=True):
        print("Cleared Alarm 1 flag")
    if rtc.alarm2(clear=True):
        print("Cleared Alarm 2 flag")

else:
    # First boot - set up RTC and configure alarm
    print("First boot - setting up RTC")

    # Clear any existing alarm flags first
    rtc.alarm1(clear=True)
    rtc.alarm2(clear=True)

    # Set RTC time (use autoTime or set manually)
    rtc.autoTime()

    # Display current time
    rtc.update()
    print(
        "Current RTC time: {0}:{1:02d}:{2:02d}".format(
            rtc.hour(), rtc.minute(), rtc.second()
        )
    )

    # Configure alarm to trigger in 30 seconds from now
    current_second = rtc.second()
    alarm_second = (current_second + 30) % 60
    alarm_minute = rtc.minute() + ((current_second + 30) // 60)

    if alarm_minute >= 60:
        alarm_minute %= 60

    # Set alarm 1 to trigger at specific second (ignore minutes, hours, date)
    # 255 = "don't care" for that field
    rtc.setAlarm1(second=alarm_second, minute=255, hour=255, date=255, day=False)

    # Enable alarm 1 interrupt - THIS IS CRITICAL!
    rtc.enableAlarmInterrupt(alarm1=True, alarm2=False)

    # Verify alarm is set correctly
    print("Alarm set to trigger at second:", alarm_second)

# Configure the interrupt pin as input with pullup
wakeup_pin = machine.Pin(WAKEUP_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

# Configure deep sleep with RTC alarm wakeup
print("Going to deep sleep...")
time.sleep(1)

# Set up wakeup source - use external pin triggered by RTC alarm
# The DS3234 INT pin goes LOW when alarm triggers
esp32.wake_on_ext0(pin=wakeup_pin, level=esp32.WAKEUP_ALL_LOW)

# Go to deep sleep
machine.deepsleep()
