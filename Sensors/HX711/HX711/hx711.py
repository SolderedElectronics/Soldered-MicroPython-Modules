# FILE: hx711.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the Soldered HX711 Load Cell amplifier with Qwiic/I2C
# LAST UPDATED: 2026-05-21

from machine import I2C, Pin
from os import uname

# Default I2C address
HX711_DEFAULT_ADDRESS = 0x30

# Gain settings
GAIN_128 = 1  # Channel A, gain 128 (default)
GAIN_64  = 3  # Channel A, gain 64
GAIN_32  = 2  # Channel B, gain 32

# Command bytes sent to board firmware
_SET_GAIN_32   = 1
_SET_GAIN_64   = 2
_SET_GAIN_128  = 3
_SET_SLEEP_ON  = 4
_SET_SLEEP_OFF = 5


class HX711:
    """
    MicroPython class for the Soldered HX711 Load Cell amplifier (Qwiic/I2C version).
    Communicates over I2C.
    """

    def __init__(self, i2c=None, address=HX711_DEFAULT_ADDRESS):
        """
        Initialize the HX711.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address of the device (default 0x30)
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            elif uname().sysname == "esp8266":
                self.i2c = I2C(scl=Pin(5), sda=Pin(4))
            else:
                raise Exception("Board not recognized, please pass an I2C object manually")

        self.address = address
        self._gain = GAIN_128
        self._scale = 1.0
        self._offset = 0.0

    def getRawReading(self):
        """Read raw 32-bit signed value from HX711 over I2C."""
        try:
            data = self.i2c.readfrom(self.address, 4)
            value = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]
            if value & 0x80000000:
                value -= 0x100000000
            return value
        except:
            return 0

    def getAveragedReading(self, numReadings=1):
        """Average numReadings raw readings and return as integer."""
        total = 0.0
        for _ in range(numReadings):
            total += self.getRawReading()
        return int(total / numReadings)

    def getOffsettedReading(self, numReadings=1):
        """Return averaged reading minus offset."""
        return self.getAveragedReading(numReadings) - self._offset

    def getReadingInUnits(self, numReadings=1):
        """Return offsetted reading divided by scale (in user-defined units)."""
        return self.getOffsettedReading(numReadings) / self._scale

    def setZero(self):
        """Set zero offset using 15 averaged readings. Load cell must be unloaded when calling this."""
        self.setOffset(self.getAveragedReading(15))

    def setGain(self, gain):
        """Set ADC gain. Use GAIN_128, GAIN_64, or GAIN_32."""
        self._gain = gain
        if gain == GAIN_32:
            cmd = _SET_GAIN_32
        elif gain == GAIN_64:
            cmd = _SET_GAIN_64
        else:
            cmd = _SET_GAIN_128
        try:
            self.i2c.writeto(self.address, bytes([cmd]))
        except:
            pass

    def getGain(self):
        """Return currently set gain value."""
        return self._gain

    def setScale(self, scale):
        """Set scale divisor for getReadingInUnits."""
        self._scale = scale

    def getScale(self):
        """Return currently set scale."""
        return self._scale

    def setOffset(self, offset):
        """Set offset for getOffsettedReading and getReadingInUnits."""
        self._offset = offset

    def getOffset(self):
        """Return currently set offset."""
        return self._offset

    def setDeepSleep(self, sleep):
        """Put HX711 to sleep (True) or wake it (False)."""
        cmd = _SET_SLEEP_ON if sleep else _SET_SLEEP_OFF
        try:
            self.i2c.writeto(self.address, bytes([cmd]))
        except:
            pass
