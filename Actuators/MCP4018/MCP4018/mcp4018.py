# FILE: mcp4018.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython driver for MCP4018 digital potentiometer
# LAST UPDATED: 2026-05-26

from machine import I2C, Pin
from os import uname

MCP4018_ADDR = 0x2F
MCP4018_MAX_VALUE = 127


class MCP4018:
    """MicroPython driver for MCP4018 digital potentiometer (I2C)."""

    def __init__(self, i2c=None):
        """
        Initialize MCP4018.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self._addr = MCP4018_ADDR
        self._value = self._readWiper()

    def _readWiper(self):
        """Read current wiper value from chip."""
        try:
            data = self.i2c.readfrom(self._addr, 1)
            return data[0] & 0x7F
        except OSError as e:
            raise Exception("I2C read error: {}".format(e))

    def _writeWiper(self, value):
        """Write wiper value to chip."""
        try:
            self.i2c.writeto(self._addr, bytes([value & 0x7F]))
        except OSError as e:
            raise Exception("I2C write error: {}".format(e))

    def setWiperPercent(self, percent: float) -> bool:
        """
        Set wiper position as percentage.

        :param percent: float, 0.0-100.0
        :returns: bool, True on success, False if out of range
        """
        if percent < 0.0 or percent > 100.0:
            return False
        self._value = int((percent / 100.0) * MCP4018_MAX_VALUE)
        self._writeWiper(self._value)
        return True

    def setWiperValue(self, value: int) -> bool:
        """
        Set wiper position as raw value.

        :param value: int, 0-127
        :returns: bool, True on success, False if out of range
        """
        if value < 0 or value > MCP4018_MAX_VALUE:
            return False
        self._value = value
        self._writeWiper(self._value)
        return True

    def getWiperPercent(self) -> float:
        """
        Get wiper position as percentage.

        :returns: float, 0.0-100.0
        """
        return (self._value / MCP4018_MAX_VALUE) * 100.0

    def getWiperValue(self) -> int:
        """
        Get wiper position as raw value.

        :returns: int, 0-127
        """
        return self._value

    def increment(self) -> bool:
        """
        Increment wiper by one step.

        :returns: bool, True on success, False if already at max
        """
        if self._value >= MCP4018_MAX_VALUE:
            return False
        self._value += 1
        self._writeWiper(self._value)
        return True

    def decrement(self) -> bool:
        """
        Decrement wiper by one step.

        :returns: bool, True on success, False if already at min
        """
        if self._value <= 0:
            return False
        self._value -= 1
        self._writeWiper(self._value)
        return True
