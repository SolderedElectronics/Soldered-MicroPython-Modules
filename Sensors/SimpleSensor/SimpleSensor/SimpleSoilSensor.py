# FILE: SimpleSoilSensor.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for Soldered Simple Soil Humidity Sensor
# LAST UPDATED: 2026-05-25

from SimpleSensor import SimpleSensor
from SimpleSensor import SIMPLE_SENSOR_I2C_ADDR


class SimpleSoilSensor(SimpleSensor):
    """
    MicroPython class for Soldered Simple Soil Humidity Sensor.
    Detects soil moisture level using resistive sensing.
    Works in native mode (ADC + digital pin) or easyC I2C mode.
    """

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=SIMPLE_SENSOR_I2C_ADDR):
        """
        Initialize the soil humidity sensor.
        Pass analog_pin for native mode, or leave empty for easyC I2C mode.

        :param analog_pin: GPIO pin number for analog input, native mode (optional)
        :param digital_pin: GPIO pin number for digital input, native mode (optional)
        :param i2c: Initialized I2C object for easyC mode (optional, auto-detected on ESP32)
        :param address: I2C address for easyC mode, default 0x30, selectable 0x30-0x37
        """
        super().__init__(analog_pin=analog_pin, digital_pin=digital_pin, i2c=i2c, address=address)

    def isMoist(self) -> bool:
        """
        Check if soil moisture is detected above threshold.
        In native mode with digital pin: reads digital output (active low).
        In native mode without digital pin: compares getValue() against threshold.
        In easyC mode: compares getValue() against threshold.

        :returns: bool, True if moisture detected
        """
        if self.native and self._digitalPin is not None:
            return not self._digitalPin.value()
        return self.getValue() > self._threshold
