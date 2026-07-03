# FILE: SliderPotentiometer.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the Slider Potentiometer with Qwiic.
# LAST UPDATED: 2026-04-30

from machine import ADC, Pin, I2C
from os import uname
import struct


class SliderPotentiometer:
    """
    Base class for slider potentiometer implementations.
    Provides a common interface for analog and Qwiic variants.
    """

    def get_value(self):
        """
        Read the raw value of the potentiometer.

        :return: Raw potentiometer reading
        """
        raise NotImplementedError

    def min_value(self):
        """
        Get the minimum possible potentiometer reading.

        :return: Minimum value (always 0)
        """
        return 0

    def max_value(self):
        """
        Get the maximum possible potentiometer reading.

        :return: Maximum value
        """
        raise NotImplementedError

    def get_percentage(self):
        """
        Get the current potentiometer position as a percentage.

        :return: Position as integer percentage (0-100)
        """
        return int(100 * (self.get_value() / self.max_value()))


class AnalogSliderPotentiometer(SliderPotentiometer):
    """
    Slider potentiometer read via onboard ADC pin.
    """

    def __init__(self, pin):
        """
        Initialize the analog slider potentiometer.

        :param pin: GPIO pin number connected to the potentiometer wiper
        :param calibrated_min: Raw ADC value at physical minimum (default 0)
        :param calibrated_max: Raw ADC value at physical maximum (default 65535);
                               tune this down if the slider saturates before full travel
        """
        self._adc = ADC(Pin(pin))

    def get_value(self):
        """
        Read the raw 16-bit ADC value.

        :return: Raw ADC reading (0-65535)
        """
        return self._adc.read_u16()

    def max_value(self):
        """
        Get the calibrated maximum value.

        :return: Calibrated maximum ADC reading
        """
        return 65536

    def get_percentage(self):
        """
        Get the current potentiometer position as a percentage, clamped to calibrated range.

        :return: Position as integer percentage (0-100)
        """
        raw = self.get_value()
        clamped = max(self.min_value, min(self.max_value, raw))
        return int(100 * (clamped - self.min_value) / self.max_value)


class QwiicSliderPotentiometer(SliderPotentiometer):
    """
    Slider potentiometer read via Qwiic (I2C) interface.
    Compatible with the Soldered easyC slider potentiometer breakout.

    Default I2C address: 0x30
    """

    _ANALOG_READ_REG = 0x00
    _DEFAULT_ADDRESS = 0x30

    def __init__(self, i2c=None, address=_DEFAULT_ADDRESS):
        """
        Initialize the Qwiic slider potentiometer.

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

    def get_value(self):
        """
        Read the raw potentiometer value over Qwiic.

        :return: Raw potentiometer reading (0-1024)
        """
        self._i2c.writeto(self._address, bytes([self._ANALOG_READ_REG]))
        raw = self._i2c.readfrom(self._address, 2)
        return struct.unpack_from("<H", raw)[0]

    def max_value(self):
        """
        Get the maximum possible potentiometer reading.

        :return: Maximum value (1024)
        """
        return 1024
