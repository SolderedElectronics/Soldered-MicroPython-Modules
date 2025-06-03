# FILE: shtc3.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython library for the SHTC3 temperature and humidity sensor
# LAST UPDATED: 2025-05-23

from machine import I2C, Pin
import time
from os import uname

# I2C address of the SHTC3 sensor
I2C_ADDR = 0x70

# Sensor command constants
SHTC3_SLEEP = 0xB098  # Put sensor to sleep
SHTC3_WAKEUP = 0x3517  # Wake sensor from sleep
SHTC3_RESET = 0x805D  # Soft reset
SHTC3_ID = 0xEFC8  # Read sensor ID
SHTC3_READ = 0x7CA2  # Measure T+RH (normal power)
SHTC3_READ_LP = 0x6458  # Measure T+RH (low power)

# Conversion constants
H_K = 0.001525878906  # Humidity scaling factor
T_K = 0.002670288086  # Temperature scaling factor
T_MIN = 45.0  # Temperature offset


class SHTC3:
    """Class for interfacing with the SHTC3 temperature and humidity sensor over I2C."""

    def __init__(self, i2c=None):
        """Initialize the sensor with an I2C interface."""
        if i2c != None:
            self.i2c = i2c
        else:
            if uname().sysname == "esp32" or uname().sysname == "esp8266":
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")
        self._t = 0
        self._h = 0

    def crc8(self, data):
        """Calculate CRC-8 for data using polynomial 0x31 (x^8 + x^5 + x^4 + 1)."""
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = ((crc << 1) ^ 0x31) if (crc & 0x80) else (crc << 1)
                crc &= 0xFF
        return crc

    def check_crc(self, data):
        """Check if the CRC byte of the 3-byte data block is valid."""
        return self.crc8(data[:2]) == data[2]

    def twi_command(self, cmd, stop=True):
        """Send a 16-bit command to the sensor via I2C."""
        try:
            self.i2c.writeto(I2C_ADDR, bytes([cmd >> 8, cmd & 0xFF]), stop)
            return True
        except OSError:
            return False

    def twi_transfer(self, cmd, length, pause_ms=0):
        """
        Send a command and read a response from the sensor.
        Returns `None` if communication fails or response is the wrong length.
        """
        if not self.twi_command(cmd, stop=False):
            return None
        if pause_ms > 0:
            time.sleep_ms(pause_ms)
        try:
            data = self.i2c.readfrom(I2C_ADDR, length)
            return data if len(data) == length else None
        except OSError:
            return None

    def wakeup(self):
        """Wake the sensor from sleep mode."""
        return self.twi_command(SHTC3_WAKEUP)

    def reset(self):
        """Perform a soft reset of the sensor."""
        return self.twi_command(SHTC3_RESET)

    def sleep(self):
        """Put the sensor into sleep mode to reduce power consumption."""
        return self.twi_command(SHTC3_SLEEP)

    def begin(self, do_sample=True):
        """
        Initialize the sensor and verify communication.
        Optionally performs an initial measurement.
        Returns True if successful, False otherwise.
        """
        time.sleep_us(240)
        if not self.wakeup():
            return False

        id_data = self.twi_transfer(SHTC3_ID, 3, pause_ms=1)
        if not id_data or not self.check_crc(id_data):
            return False

        sig_valid = (id_data[0] & 0b00001000) and (
            (id_data[1] & 0b00111111) == 0b00000111
        )
        if not sig_valid:
            return False

        if not self.reset():
            return False

        if do_sample and not self.sample():
            return False

        return self.sleep()

    def sample(self, readcmd=SHTC3_READ, pause=15):
        """
        Perform a temperature and humidity measurement.
        Returns True if successful and data is valid.
        """
        if not self.wakeup():
            return False
        data = self.twi_transfer(readcmd, 6, pause)
        self.sleep()
        if not data or not self.check_crc(data) or not self.check_crc(data[3:]):
            return False

        self._t = (data[0] << 8) | data[1]
        self._h = (data[3] << 8) | data[4]
        return True

    def readTemperature(self):
        """
        Return the last measured temperature in degrees Celsius.
        Call sample() before to update the value.
        """
        return (self._t * T_K) - T_MIN

    def readHumidity(self):
        """
        Return the last measured relative humidity in %RH.
        Call sample() before to update the value.
        """
        return self._h * H_K
