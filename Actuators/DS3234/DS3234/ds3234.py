# FILE: ds3234.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Module for the Soldered DS3234 RTC Breakout board 
# LAST UPDATED: 2025-09-15 

import machine
import time
import struct
from micropython import const

# Constants from the header file
TWELVE_HOUR_MODE = const(1 << 6)
TWELVE_HOUR_PM = const(1 << 5)

DS3234_AM = False
DS3234_PM = True

SQW_CONTROL_MASK = const(0xE3)
SQW_ENABLE_BIT = const(1 << 2)

ALARM_MODE_BIT = const(1 << 7)
ALARM_DAY_BIT = const(1 << 6)
ALARM_1_FLAG_BIT = const(1 << 0)
ALARM_2_FLAG_BIT = const(1 << 1)
ALARM_INTCN_BIT = const(1 << 2)

TIME_ARRAY_LENGTH = const(7)

# Time order constants
TIME_SECONDS = const(0)
TIME_MINUTES = const(1)
TIME_HOURS = const(2)
TIME_DAY = const(3)
TIME_DATE = const(4)
TIME_MONTH = const(5)
TIME_YEAR = const(6)

# SQW rate constants
SQW_SQUARE_1 = const(0)
SQW_SQUARE_1K = const(1)
SQW_SQUARE_4K = const(2)
SQW_SQUARE_8K = const(3)

# DS3234 register addresses
DS3234_REGISTER_SECONDS = const(0x00)
DS3234_REGISTER_MINUTES = const(0x01)
DS3234_REGISTER_HOURS = const(0x02)
DS3234_REGISTER_DAY = const(0x03)
DS3234_REGISTER_DATE = const(0x04)
DS3234_REGISTER_MONTH = const(0x05)
DS3234_REGISTER_YEAR = const(0x06)
DS3234_REGISTER_A1SEC = const(0x07)
DS3234_REGISTER_A1MIN = const(0x08)
DS3234_REGISTER_A1HR = const(0x09)
DS3234_REGISTER_A1DA = const(0x0A)
DS3234_REGISTER_A2MIN = const(0x0B)
DS3234_REGISTER_A2HR = const(0x0C)
DS3234_REGISTER_A2DA = const(0x0D)
DS3234_REGISTER_CONTROL = const(0x0E)
DS3234_REGISTER_STATUS = const(0x0F)
DS3234_REGISTER_XTAL = const(0x10)
DS3234_REGISTER_TEMPM = const(0x11)
DS3234_REGISTER_TEMPL = const(0x12)
DS3234_REGISTER_TEMPEN = const(0x13)
DS3234_REGISTER_RESERV1 = const(0x14)
DS3234_REGISTER_RESERV2 = const(0x15)
DS3234_REGISTER_RESERV3 = const(0x16)
DS3234_REGISTER_RESERV4 = const(0x17)
DS3234_REGISTER_SRAMA = const(0x18)
DS3234_REGISTER_SRAMD = const(0x19)

DS3234_REGISTER_BASE = DS3234_REGISTER_SECONDS

# Day conversion arrays
dayIntToStr = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday"
]

dayIntToChar = ['U', 'M', 'T', 'W', 'R', 'F', 'S']


class DS3234:
    def __init__(self, spi, cs_pin):
        self.spi = spi
        self.cs_pin = cs_pin
        self._time = [0] * TIME_ARRAY_LENGTH
        self._pm = False
        
        # Initialize CS pin
        self.cs_pin.init(machine.Pin.OUT)
        self.cs_pin.value(1)
    
    def _spi_write_bytes(self, reg, values):
        """Write bytes to SPI device, incrementing from a register"""
        write_reg = reg | 0x80
        self.cs_pin.value(0)
        self.spi.write(bytearray([write_reg]))
        self.spi.write(bytearray(values))
        self.cs_pin.value(1)
    
    def _spi_write_byte(self, reg, value):
        """Write a byte to an SPI device's register"""
        write_reg = reg | 0x80
        self.cs_pin.value(0)
        self.spi.write(bytearray([write_reg, value]))
        self.cs_pin.value(1)
    
    def _spi_read_byte(self, reg):
        """Read a byte from an SPI device's register"""
        self.cs_pin.value(0)
        self.spi.write(bytearray([reg]))
        value = self.spi.read(1)[0]
        self.cs_pin.value(1)
        return value
    
    def _spi_read_bytes(self, reg, length):
        """Read bytes from an SPI device, incrementing from a register"""
        self.cs_pin.value(0)
        self.spi.write(bytearray([reg]))
        values = self.spi.read(length)
        self.cs_pin.value(1)
        return values
    
    @staticmethod
    def BCDtoDEC(val):
        """Convert binary-coded decimal (BCD) to decimal"""
        return ((val // 0x10) * 10) + (val % 0x10)
    
    @staticmethod
    def DECtoBCD(val):
        """Convert decimal to binary-coded decimal (BCD)"""
        return ((val // 10) * 0x10) + (val % 10)
    
    def setTime(self, sec, min, hour, day, date, month, year):
        """Set time and date/day registers of DS3234"""
        self._time[TIME_SECONDS] = self.DECtoBCD(sec)
        self._time[TIME_MINUTES] = self.DECtoBCD(min)
        self._time[TIME_HOURS] = self.DECtoBCD(hour)
        self._time[TIME_DAY] = self.DECtoBCD(day)
        self._time[TIME_DATE] = self.DECtoBCD(date)
        self._time[TIME_MONTH] = self.DECtoBCD(month)
        self._time[TIME_YEAR] = self.DECtoBCD(year)
        
        self._spi_write_bytes(DS3234_REGISTER_BASE, self._time)
    
    def setTime12h(self, sec, min, hour12, pm, day, date, month, year):
        """Set time and date/day registers of DS3234 in 12-hour format"""
        self._time[TIME_SECONDS] = self.DECtoBCD(sec)
        self._time[TIME_MINUTES] = self.DECtoBCD(min)
        self._time[TIME_HOURS] = self.DECtoBCD(hour12)
        self._time[TIME_HOURS] |= TWELVE_HOUR_MODE
        if pm:
            self._time[TIME_HOURS] |= TWELVE_HOUR_PM
        self._time[TIME_DAY] = self.DECtoBCD(day)
        self._time[TIME_DATE] = self.DECtoBCD(date)
        self._time[TIME_MONTH] = self.DECtoBCD(month)
        self._time[TIME_YEAR] = self.DECtoBCD(year)
        
        self._spi_write_bytes(DS3234_REGISTER_BASE, self._time)
    
    def setTimeArray(self, time_array):
        """Set time and date/day registers of DS3234 (using data array)"""
        if len(time_array) != TIME_ARRAY_LENGTH:
            return
        
        self._spi_write_bytes(DS3234_REGISTER_BASE, time_array)
    
    def autoTime(self):
        """Fill DS3234 time registers with current time/date"""
        # Get current time from MicroPython's RTC
        rtc = machine.RTC()
        now = rtc.datetime()
        
        # Format: (year, month, day, weekday, hour, minute, second, microsecond)
        year = now[0] % 100  # Convert to 2-digit year
        month = now[1]
        day = now[2]
        weekday = now[3] + 1  # MicroPython weekday: 0-6 for Monday-Sunday, DS3234: 1-7 for Sunday-Saturday
        if weekday > 7:
            weekday = 1
        
        hour = now[4]
        minute = now[5]
        second = now[6]
        
        # Convert to 12-hour format if needed
        if self.is12hour():
            pm_bit = 0
            if hour <= 11:
                if hour == 0:
                    hour = 12
            else:
                pm_bit = TWELVE_HOUR_PM
                if hour >= 13:
                    hour -= 12
            
            hour = self.DECtoBCD(hour)
            hour |= pm_bit
            hour |= TWELVE_HOUR_MODE
        else:
            hour = self.DECtoBCD(hour)
        
        self._time[TIME_SECONDS] = self.DECtoBCD(second)
        self._time[TIME_MINUTES] = self.DECtoBCD(minute)
        self._time[TIME_HOURS] = hour
        self._time[TIME_MONTH] = self.DECtoBCD(month)
        self._time[TIME_DATE] = self.DECtoBCD(day)
        self._time[TIME_YEAR] = self.DECtoBCD(year)
        self._time[TIME_DAY] = self.DECtoBCD(weekday)
        
        self._spi_write_bytes(DS3234_REGISTER_BASE, self._time)
    
    def update(self):
        """Read all time/date registers and update the _time array"""
        rtc_reads = self._spi_read_bytes(DS3234_REGISTER_BASE, TIME_ARRAY_LENGTH)
        
        for i in range(TIME_ARRAY_LENGTH):
            self._time[i] = rtc_reads[i]
        
        if self._time[TIME_HOURS] & TWELVE_HOUR_MODE:
            if self._time[TIME_HOURS] & TWELVE_HOUR_PM:
                self._pm = True
            else:
                self._pm = False
            
            self._time[TIME_HOURS] &= 0x1F  # Mask out 24-hour bit, am/pm from hours
        else:
            self._time[TIME_HOURS] &= 0x3F  # Mask out 24-hour bit from hours
    
    def second(self):
        return self.BCDtoDEC(self._time[TIME_SECONDS])
    
    def minute(self):
        return self.BCDtoDEC(self._time[TIME_MINUTES])
    
    def hour(self):
        return self.BCDtoDEC(self._time[TIME_HOURS])
    
    def day(self):
        return self.BCDtoDEC(self._time[TIME_DAY])
    
    def dayChar(self):
        day_val = self.BCDtoDEC(self._time[TIME_DAY])
        if 1 <= day_val <= 7:
            return dayIntToChar[day_val - 1]
        return '?'  # Or handle error appropriately

    def dayStr(self):
        day_val = self.BCDtoDEC(self._time[TIME_DAY])
        if 1 <= day_val <= 7:
            return dayIntToStr[day_val - 1]
        return "Unknown"  # Or handle error appropriately
    
    def date(self):
        return self.BCDtoDEC(self._time[TIME_DATE])
    
    def month(self):
        return self.BCDtoDEC(self._time[TIME_MONTH])
    
    def year(self):
        return self.BCDtoDEC(self._time[TIME_YEAR])
    
    def getSecond(self):
        self._time[TIME_SECONDS] = self._spi_read_byte(DS3234_REGISTER_SECONDS)
        return self.BCDtoDEC(self._time[TIME_SECONDS])
    
    def getMinute(self):
        self._time[TIME_MINUTES] = self._spi_read_byte(DS3234_REGISTER_MINUTES)
        return self.BCDtoDEC(self._time[TIME_MINUTES])
    
    def getHour(self):
        hour_register = self._spi_read_byte(DS3234_REGISTER_HOURS)
        
        if hour_register & TWELVE_HOUR_MODE:
            hour_register &= 0x1F  # Mask out am/pm, 24-hour bit
        self._time[TIME_HOURS] = hour_register
        
        return self.BCDtoDEC(self._time[TIME_HOURS])
    
    def getDay(self):
        self._time[TIME_DAY] = self._spi_read_byte(DS3234_REGISTER_DAY)
        return self.BCDtoDEC(self._time[TIME_DAY])
    
    def getDate(self):
        self._time[TIME_DATE] = self._spi_read_byte(DS3234_REGISTER_DATE)
        return self.BCDtoDEC(self._time[TIME_DATE])
    
    def getMonth(self):
        self._time[TIME_MONTH] = self._spi_read_byte(DS3234_REGISTER_MONTH)
        self._time[TIME_MONTH] &= 0x7F  # Mask out century bit
        return self.BCDtoDEC(self._time[TIME_MONTH])
    
    def getYear(self):
        self._time[TIME_YEAR] = self._spi_read_byte(DS3234_REGISTER_YEAR)
        return self.BCDtoDEC(self._time[TIME_YEAR])
    
    def setSecond(self, s):
        if s <= 59:
            _s = self.DECtoBCD(s)
            self._spi_write_byte(DS3234_REGISTER_SECONDS, _s)
    
    def setMinute(self, m):
        if m <= 59:
            _m = self.DECtoBCD(m)
            self._spi_write_byte(DS3234_REGISTER_MINUTES, _m)
    
    def setHour(self, h):
        if h <= 23:
            _h = self.DECtoBCD(h)
            self._spi_write_byte(DS3234_REGISTER_HOURS, _h)
    
    def setDay(self, d):
        if 1 <= d <= 7:
            _d = self.DECtoBCD(d)
            self._spi_write_byte(DS3234_REGISTER_DAY, _d)
    
    def setDate(self, d):
        if d <= 31:
            _d = self.DECtoBCD(d)
            self._spi_write_byte(DS3234_REGISTER_DATE, _d)
    
    def setMonth(self, mo):
        if 1 <= mo <= 12:
            _mo = self.DECtoBCD(mo)
            self._spi_write_byte(DS3234_REGISTER_MONTH, _mo)
    
    def setYear(self, y):
        if y <= 99:
            _y = self.DECtoBCD(y)
            self._spi_write_byte(DS3234_REGISTER_YEAR, _y)
    
    def set12hour(self, enable12=True):
        if enable12:
            self.set24hour(False)
        else:
            self.set24hour(True)
    
    def set24hour(self, enable24=True):
        hour_register = self._spi_read_byte(DS3234_REGISTER_HOURS)
        
        hour12 = hour_register & TWELVE_HOUR_MODE
        if (hour12 and not enable24) or (not hour12 and enable24):
            return
        
        if enable24:
            old_hour = hour_register & 0x1F  # Mask out am/pm and 12-hour mode
            old_hour = self.BCDtoDEC(old_hour)  # Convert to decimal
            new_hour = old_hour
            
            hour_pm = hour_register & TWELVE_HOUR_PM
            if hour_pm and old_hour >= 1:
                new_hour += 12
            elif not hour_pm and old_hour == 12:
                new_hour = 0
            new_hour = self.DECtoBCD(new_hour)
        else:
            old_hour = hour_register & 0x3F  # Mask out am/pm and 12-hour mode
            old_hour = self.BCDtoDEC(old_hour)  # Convert to decimal
            new_hour = old_hour
            
            if old_hour == 0:
                new_hour = 12
            elif old_hour >= 13:
                new_hour -= 12
            
            new_hour = self.DECtoBCD(new_hour)
            new_hour |= TWELVE_HOUR_MODE  # Set bit 6 to set 12-hour mode
            if old_hour >= 12:
                new_hour |= TWELVE_HOUR_PM  # Set PM bit if necessary
        
        self._spi_write_byte(DS3234_REGISTER_HOURS, new_hour)
    
    def is12hour(self):
        hour_register = self._spi_read_byte(DS3234_REGISTER_HOURS)
        return bool(hour_register & TWELVE_HOUR_MODE)
    
    def pm(self):
        hour_register = self._spi_read_byte(DS3234_REGISTER_HOURS)
        return bool(hour_register & TWELVE_HOUR_PM)
    
    def enable(self):
        control_register = self._spi_read_byte(DS3234_REGISTER_CONTROL)
        control_register &= ~(1 << 7)
        self._spi_write_byte(DS3234_REGISTER_CONTROL, control_register)
    
    def disable(self):
        control_register = self._spi_read_byte(DS3234_REGISTER_CONTROL)
        control_register |= (1 << 7)
        self._spi_write_byte(DS3234_REGISTER_CONTROL, control_register)
        
    def setAlarm1(self, second=255, minute=255, hour=255, date=255, day=False):
        # Read current alarm settings
        alarm_reg = list(self._spi_read_bytes(DS3234_REGISTER_A1SEC, 4))
        
        # Set seconds
        if second == 255:
            alarm_reg[0] |= ALARM_MODE_BIT  # Don't care about seconds
        else:
            alarm_reg[0] &= ~ALARM_MODE_BIT  # Match specific seconds
            alarm_reg[0] = self.DECtoBCD(second)
        
        # Set minutes
        if minute == 255:
            alarm_reg[1] |= ALARM_MODE_BIT  # Don't care about minutes
        else:
            alarm_reg[1] &= ~ALARM_MODE_BIT  # Match specific minutes
            alarm_reg[1] = self.DECtoBCD(minute)
        
        # Set hours
        if hour == 255:
            alarm_reg[2] |= ALARM_MODE_BIT  # Don't care about hours
        else:
            alarm_reg[2] &= ~ALARM_MODE_BIT  # Match specific hours
            alarm_reg[2] = self.DECtoBCD(hour)
        
        # Set day/date
        if date == 255:
            alarm_reg[3] |= ALARM_MODE_BIT  # Don't care about day/date
        else:
            alarm_reg[3] &= ~ALARM_MODE_BIT  # Match specific day/date
            if day:
                alarm_reg[3] |= ALARM_DAY_BIT  # Day of week (1-7)
            else:
                alarm_reg[3] &= ~ALARM_DAY_BIT  # Date of month (1-31)
            alarm_reg[3] = self.DECtoBCD(date)
        
        self._spi_write_bytes(DS3234_REGISTER_A1SEC, alarm_reg)

    def setAlarm2(self, minute=255, hour=255, date=255, day=False):
        # Read current alarm settings (Alarm2 has no seconds)
        alarm_reg = list(self._spi_read_bytes(DS3234_REGISTER_A2MIN, 3))
        
        # Set minutes
        if minute == 255:
            alarm_reg[0] |= ALARM_MODE_BIT  # Don't care about minutes
        else:
            alarm_reg[0] &= ~ALARM_MODE_BIT  # Match specific minutes
            alarm_reg[0] = self.DECtoBCD(minute)
        
        # Set hours
        if hour == 255:
            alarm_reg[1] |= ALARM_MODE_BIT  # Don't care about hours
        else:
            alarm_reg[1] &= ~ALARM_MODE_BIT  # Match specific hours
            alarm_reg[1] = self.DECtoBCD(hour)
        
        # Set day/date
        if date == 255:
            alarm_reg[2] |= ALARM_MODE_BIT  # Don't care about day/date
        else:
            alarm_reg[2] &= ~ALARM_MODE_BIT  # Match specific day/date
            if day:
                alarm_reg[2] |= ALARM_DAY_BIT  # Day of week (1-7)
            else:
                alarm_reg[2] &= ~ALARM_DAY_BIT  # Date of month (1-31)
            alarm_reg[2] = self.DECtoBCD(date)
        
        self._spi_write_bytes(DS3234_REGISTER_A2MIN, alarm_reg)
        
    def alarm1(self, clear:bool):
        statusRegister = self._spi_read_byte(DS3234_REGISTER_STATUS)
        if (statusRegister & ALARM_1_FLAG_BIT) != 0:  # Fixed comparison
            if clear:
                # Clear the alarm flag by writing 0 to it
                statusRegister &= ~ALARM_1_FLAG_BIT
                self._spi_write_byte(DS3234_REGISTER_STATUS, statusRegister)
            return True
        return False

    def alarm2(self, clear:bool):
        statusRegister = self._spi_read_byte(DS3234_REGISTER_STATUS)
        if (statusRegister & ALARM_2_FLAG_BIT) != 0:  # Fixed comparison
            if clear:
                # Clear the alarm flag by writing 0 to it
                statusRegister &= ~ALARM_2_FLAG_BIT
                self._spi_write_byte(DS3234_REGISTER_STATUS, statusRegister)
            return True
        return False

    def enableAlarmInterrupt(self, alarm1=True, alarm2=True):
        """Enable the SQW interrupt output on one, or both, alarms"""
        control_register = self._spi_read_byte(DS3234_REGISTER_CONTROL)
        
        # Set INTCN bit to enable alarm interrupts (SQW pin as interrupt)
        control_register |= ALARM_INTCN_BIT
        
        # Enable the specific alarms
        if alarm1:
            control_register |= (1 << 0)  # Set A1IE bit
        else:
            control_register &= ~(1 << 0)  # Clear A1IE bit
            
        if alarm2:
            control_register |= (1 << 1)  # Set A2IE bit
        else:
            control_register &= ~(1 << 1)  # Clear A2IE bit
            
        self._spi_write_byte(DS3234_REGISTER_CONTROL, control_register)

    def writeSQW(self, value):
        """Set the SQW pin high, low, or to one of the square wave frequencies"""
        control_register = self._spi_read_byte(DS3234_REGISTER_CONTROL)
        
        control_register &= SQW_CONTROL_MASK  # Mask out RS1, RS2 bits (bits 3 and 4)
        control_register |= (value << 3)      # Add rate bits, shift left 3
        control_register &= ~SQW_ENABLE_BIT   # Clear INTCN bit to enable SQW output
        self._spi_write_byte(DS3234_REGISTER_CONTROL, control_register)

    def temperature(self):
        """Read the DS3234's die-temperature in degrees Celsius"""
        temp_register = self._spi_read_bytes(DS3234_REGISTER_TEMPM, 2)
        
        integer = temp_register[0]
        if integer > 127:  # Handle negative temperatures (two's complement)
            integer = integer - 256
        
        fractional = (temp_register[1] >> 6) * 0.25
        return integer + fractional
    
    def writeToSRAM(self, address, data):
        """Write a single byte to SRAM"""
        self._spi_write_byte(DS3234_REGISTER_SRAMA, address)
        self._spi_write_byte(DS3234_REGISTER_SRAMD, data)

    def writeToSRAMBuffer(self, address, values):
        """Write multiple bytes to SRAM"""
        self._spi_write_byte(DS3234_REGISTER_SRAMA, address)
        self._spi_write_bytes(DS3234_REGISTER_SRAMD, values)

    def writeToSRAMValue(self, address, value, data_type):
        """Write a value of specified type to SRAM"""
        if data_type == 'uint8':
            buf = bytes([value & 0xFF])
        elif data_type == 'uint16':
            buf = struct.pack('<H', value)
        elif data_type == 'uint32':
            buf = struct.pack('<I', value)
        elif data_type == 'uint64':
            buf = struct.pack('<Q', value)
        elif data_type == 'int8':
            buf = struct.pack('<b', value)
        elif data_type == 'int16':
            buf = struct.pack('<h', value)
        elif data_type == 'int32':
            buf = struct.pack('<i', value)
        elif data_type == 'int64':
            buf = struct.pack('<q', value)
        elif data_type == 'float':
            buf = struct.pack('<f', value)
        elif data_type == 'double':
            buf = struct.pack('<d', value)
        else:
            raise ValueError("Unsupported data type")
        
        self.writeToSRAMBuffer(address, buf)

    def readFromSRAM(self, address):
        """Read a single byte from SRAM"""
        self._spi_write_byte(DS3234_REGISTER_SRAMA, address)
        return self._spi_read_byte(DS3234_REGISTER_SRAMD)

    def readFromSRAMBuffer(self, address, length):
        """Read multiple bytes from SRAM"""
        self._spi_write_byte(DS3234_REGISTER_SRAMA, address)
        return self._spi_read_bytes(DS3234_REGISTER_SRAMD, length)

    def readFromSRAMValue(self, address, data_type):
        """Read a value of specified type from SRAM"""
        if data_type == 'uint8':
            length = 1
            unpack_fmt = '<B'
        elif data_type == 'uint16':
            length = 2
            unpack_fmt = '<H'
        elif data_type == 'uint32':
            length = 4
            unpack_fmt = '<I'
        elif data_type == 'uint64':
            length = 8
            unpack_fmt = '<Q'
        elif data_type == 'int8':
            length = 1
            unpack_fmt = '<b'
        elif data_type == 'int16':
            length = 2
            unpack_fmt = '<h'
        elif data_type == 'int32':
            length = 4
            unpack_fmt = '<i'
        elif data_type == 'int64':
            length = 8
            unpack_fmt = '<q'
        elif data_type == 'float':
            length = 4
            unpack_fmt = '<f'
        elif data_type == 'double':
            length = 8
            unpack_fmt = '<d'
        else:
            raise ValueError("Unsupported data type")
        
        buf = self.readFromSRAMBuffer(address, length)
        return struct.unpack(unpack_fmt, buf)[0]

    def writeToRegister(self, address, data):
        """Write to any register by address"""
        self._spi_write_byte(address, data)

    def readFromRegister(self, address):
        """Read from any register by address"""
        return self._spi_read_byte(address)
    

