# FILE: pcf85063a.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the PCF85063A RTC.
# LAST UPDATED: 2026-04-30

from machine import I2C, Pin
from os import uname

PCF85063A_I2C_ADDR = 0x51

# ctrl & status reg
PCF85063A_CTRL_1 = 0x0
PCF85063A_CTRL_2 = 0x01
PCF85063A_OFFSET = 0x02
PCF85063A_RAM_by = 0x03
# time & date reg
PCF85063A_SECOND_ADDR = 0x04
PCF85063A_MINUTE_ADDR = 0x05
PCF85063A_HOUR_ADDR = 0x06
PCF85063A_DAY_ADDR = 0x07
PCF85063A_WDAY_ADDR = 0x08
PCF85063A_MONTH_ADDR = 0x09
PCF85063A_YEAR_ADDR = 0x0A
# alarm reg
PCF85063A_SECOND_ALARM = 0x0B
PCF85063A_MINUTE_ALARM = 0x0C
PCF85063A_HOUR_ALARM = 0x0D
PCF85063A_DAY_ALARM = 0x0E
PCF85063A_WDAY_ALARM = 0x0F
# timer reg
PCF85063A_TIMER_VAL = 0x10
PCF85063A_TIMER_MODE = 0x11
PCF85063A_TIMER_TCF = 0x08
PCF85063A_TIMER_TE = 0x04
PCF85063A_TIMER_TIE = 0x02
PCF85063A_TIMER_TI_TP = 0x01

PCF85063A_ALARM = 0x80
PCF85063A_ALARM_AIE = 0x80
PCF85063A_ALARM_AF = 0x40
PCF85063A_CTRL_2_DEFAULT = 0x00
PCF85063A_TIMER_FLAG = 0x08

PCF85063A_TIMER_CLOCK_4096HZ = 0
PCF85063A_TIMER_CLOCK_64HZ = 1
PCF85063A_TIMER_CLOCK_1HZ = 2
PCF85063A_TIMER_CLOCK_1PER60HZ = 3


def bcd_to_dec(bcd):
    return ((bcd >> 4) * 10) + (bcd & 0x0F)


def dec_to_bcd(val):
    return ((val // 10) << 4) | (val % 10)


def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))


class PCF85063A:
    """
    MicroPython class for the PCF85063A real-time clock.
    Supports timekeeping, alarm generation, and countdown timer with
    interrupt output on the INT pin.
    """

    def __init__(self, i2c=None, address=PCF85063A_I2C_ADDR):
        """
        Initialize the PCF85063A RTC.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address of the device (default 0x51)
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.address = address

    # ---- time ----

    def get_time(self):
        """
        Read the current date and time from the RTC.

        :return: Tuple (year, month, day, weekday, hour, minute, second)
                 weekday is 0=Sunday, 6=Saturday
        """
        data = self.i2c.readfrom_mem(self.address, PCF85063A_SECOND_ADDR, 7)

        second = bcd_to_dec(data[0] & 0x7F)
        minute = bcd_to_dec(data[1] & 0x7F)
        hour = bcd_to_dec(data[2] & 0x3F)
        day = bcd_to_dec(data[3] & 0x3F)
        weekday = bcd_to_dec(data[4] & 0x07)
        month = bcd_to_dec(data[5] & 0x1F)
        year = bcd_to_dec(data[6]) + 1970

        return (year, month, day, weekday, hour, minute, second)

    def set_time(self, second, minute, hour, weekday, day, month, year):
        """
        Set the current date and time on the RTC.

        :param second: Seconds (0-59)
        :param minute: Minutes (0-59)
        :param hour: Hours (0-23)
        :param weekday: Day of week (0=Sunday, 6=Saturday)
        :param day: Day of month (1-31)
        :param month: Month (1-12)
        :param year: Full year (e.g. 2025); stored as offset from 1970
        """
        year_rtc = year - 1970

        data = bytes(
            [
                dec_to_bcd(second),
                dec_to_bcd(minute),
                dec_to_bcd(hour),
                dec_to_bcd(day),
                dec_to_bcd(weekday),
                dec_to_bcd(month),
                dec_to_bcd(year_rtc),
            ]
        )

        self.i2c.writeto_mem(self.address, PCF85063A_SECOND_ADDR, data)

    def get_second(self):
        """
        Read the current seconds value.

        :return: Seconds (0-59)
        """
        return self.get_time()[6]

    def get_minute(self):
        """
        Read the current minutes value.

        :return: Minutes (0-59)
        """
        return self.get_time()[5]

    def get_hour(self):
        """
        Read the current hours value.

        :return: Hours (0-23)
        """
        return self.get_time()[4]

    def get_weekday(self):
        """
        Read the current day of the week.

        :return: Weekday (0=Sunday, 6=Saturday)
        """
        return self.get_time()[3]

    def get_day(self):
        """
        Read the current day of the month.

        :return: Day (1-31)
        """
        return self.get_time()[2]

    def get_month(self):
        """
        Read the current month.

        :return: Month (1-12)
        """
        return self.get_time()[1]

    def get_year(self):
        """
        Read the current year.

        :return: Full year (e.g. 2025)
        """
        return self.get_time()[0]

    # ---- alarm ----

    def set_alarm(
        self, alarm_second, alarm_minute, alarm_hour, alarm_day, alarm_weekday
    ):
        """
        Configure the alarm and enable the alarm interrupt on the INT pin.

        Pass 99 for any field to ignore it in the alarm match — for example,
        passing 99 for alarm_hour makes the alarm fire every hour.

        :param alarm_second: Seconds to match (0-59), or 99 to ignore
        :param alarm_minute: Minutes to match (0-59), or 99 to ignore
        :param alarm_hour: Hours to match (0-23), or 99 to ignore
        :param alarm_day: Day of month to match (1-31), or 99 to ignore
        :param alarm_weekday: Day of week to match (0=Sunday, 6=Saturday), or 99 to ignore
        """

        def encode_alarm(val, min_val, max_val):
            if val < 99:
                val = max(min_val, min(val, max_val))
                return dec_to_bcd(val) & ~PCF85063A_ALARM
            else:
                return PCF85063A_ALARM

        # Enable alarm interrupt and clear any pending alarm flag
        control_2 = PCF85063A_CTRL_2_DEFAULT | PCF85063A_ALARM_AIE
        control_2 &= ~PCF85063A_ALARM_AF
        self.i2c.writeto_mem(self.address, PCF85063A_CTRL_2, bytes([control_2]))

        data = bytes(
            [
                encode_alarm(alarm_second, 0, 59),
                encode_alarm(alarm_minute, 0, 59),
                encode_alarm(alarm_hour, 0, 23),
                encode_alarm(alarm_day, 1, 31),
                encode_alarm(alarm_weekday, 0, 6),
            ]
        )

        self.i2c.writeto_mem(self.address, PCF85063A_SECOND_ALARM, data)

    def get_alarm(self):
        """
        Read the currently configured alarm fields.

        Fields that are disabled (AEN bit set) are returned as 99.

        :return: Tuple (alarm_day, alarm_weekday, alarm_hour, alarm_minute, alarm_second)
                 Any field set to 99 is not active in the alarm match.
        """

        def decode_alarm(val, mask):
            if val & PCF85063A_ALARM:
                return 99
            return bcd_to_dec(val & mask)

        data = self.i2c.readfrom_mem(self.address, PCF85063A_SECOND_ALARM, 5)

        alarm_second = decode_alarm(data[0], 0x7F)
        alarm_minute = decode_alarm(data[1], 0x7F)
        alarm_hour = decode_alarm(data[2], 0x3F)
        alarm_day = decode_alarm(data[3], 0x3F)
        alarm_weekday = decode_alarm(data[4], 0x07)

        return (alarm_day, alarm_weekday, alarm_hour, alarm_minute, alarm_second)

    def get_alarm_second(self):
        """
        Read the alarm seconds field.

        :return: Seconds (0-59), or 99 if this field is disabled
        """
        return self.get_alarm()[4]

    def get_alarm_minute(self):
        """
        Read the alarm minutes field.

        :return: Minutes (0-59), or 99 if this field is disabled
        """
        return self.get_alarm()[3]

    def get_alarm_hour(self):
        """
        Read the alarm hours field.

        :return: Hours (0-23), or 99 if this field is disabled
        """
        return self.get_alarm()[2]

    def get_alarm_weekday(self):
        """
        Read the alarm weekday field.

        :return: Weekday (0=Sunday, 6=Saturday), or 99 if this field is disabled
        """
        return self.get_alarm()[1]

    def get_alarm_day(self):
        """
        Read the alarm day-of-month field.

        :return: Day (1-31), or 99 if this field is disabled
        """
        return self.get_alarm()[0]

    def clear_alarm(self):
        """
        Clear the alarm flag (AF bit) in Control_2 to de-assert the INT pin.

        Call this after waking from deep sleep triggered by an alarm, otherwise
        the INT pin stays low and the ESP32 will wake immediately on the next
        deep sleep call instead of waiting for the next alarm.
        """
        ctrl_2 = self.i2c.readfrom_mem(self.address, PCF85063A_CTRL_2, 1)[0]
        ctrl_2 &= ~PCF85063A_ALARM_AF
        self.i2c.writeto_mem(self.address, PCF85063A_CTRL_2, bytes([ctrl_2]))

    # ---- timer ----

    def set_timer(self, source_clock, value, int_enable=False, int_pulse=False):
        """
        Configure and start the countdown timer.

        The timer counts down from value at the selected clock frequency and
        optionally pulses or holds the INT pin low when it reaches zero.

        :param source_clock: Clock source — one of PCF85063A_TIMER_CLOCK_4096HZ,
                             PCF85063A_TIMER_CLOCK_64HZ, PCF85063A_TIMER_CLOCK_1HZ,
                             or PCF85063A_TIMER_CLOCK_1PER60HZ
        :param value: Countdown start value (0-255)
        :param int_enable: True to assert INT pin when timer expires (default False)
        :param int_pulse: True for pulse mode on INT, False for level mode (default False)
        """
        # Disable timer before reconfiguring
        self.i2c.writeto_mem(self.address, PCF85063A_TIMER_MODE, bytes([0x18]))

        # Clear Control_2
        self.i2c.writeto_mem(self.address, PCF85063A_CTRL_2, bytes([0x00]))

        # Build timer mode register
        timer_mode = 0
        timer_mode |= PCF85063A_TIMER_TE  # enable timer

        if int_enable:
            timer_mode |= PCF85063A_TIMER_TIE  # interrupt enable

        if int_pulse:
            timer_mode |= PCF85063A_TIMER_TI_TP  # pulse mode

        timer_mode |= source_clock << 3  # clock source

        data = bytes([value, timer_mode])
        self.i2c.writeto_mem(self.address, PCF85063A_TIMER_VAL, data)

    def get_timer_flag(self):
        """
        Check whether the timer has expired by reading the TF flag in Control_2.

        The flag is not cleared automatically — use reset() or reconfigure the
        timer to clear it.

        :return: True if the timer has expired, False otherwise
        """
        ctrl_2 = self.i2c.readfrom_mem(self.address, PCF85063A_CTRL_2, 1)[0]
        return bool(ctrl_2 & PCF85063A_TIMER_FLAG)

    def reset(self):
        """
        Perform a software reset of the RTC by setting the SR bit in Control_1.

        This clears all registers to their power-on default values, including
        time, alarm, and timer configuration.
        """
        self.i2c.writeto_mem(self.address, PCF85063A_CTRL_1, bytes([0x18]))
