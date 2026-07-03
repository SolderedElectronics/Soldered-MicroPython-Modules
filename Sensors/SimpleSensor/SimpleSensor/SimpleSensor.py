# FILE: SimpleSensor.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython base class for Soldered Simple Sensor series (rain, soil, light, fire)
# LAST UPDATED: 2026-05-25

from machine import ADC, Pin, I2C
from os import uname

# I2C Addresses (selectable via onboard switches, 0x30-0x37)
SIMPLE_SENSOR_I2C_ADDR = 0x30

# ADC Resolution
ADC_MAX_ESP32 = 4095  # ESP32 12-bit ADC
ADC_MAX_OTHER = 1023  # 10-bit ADC (also ATtiny on easyC board)

# Pull-up resistor value in ohms (used for resistance calculation)
RES = 10000

# Default detection threshold percentage
DEFAULT_THRESHOLD = 50.0

# easyC I2C command bytes sent to onboard ATtiny firmware
CMD_SET_THRESHOLD = 0x01
CMD_SET_LED = 0x02


class SimpleSensor:
    """
    MicroPython base class for Soldered Simple Sensor series.
    Supports resistive sensors: rain, soil moisture, light, fire.
    Works in native mode (ADC + digital pin) or easyC I2C mode.
    """

    def __init__(
        self,
        analog_pin=None,
        digital_pin=None,
        i2c=None,
        address=SIMPLE_SENSOR_I2C_ADDR,
    ):
        """
        Initialize the sensor.
        Pass analog_pin for native mode, or leave empty for easyC I2C mode.

        :param analog_pin: GPIO pin number for analog input, native mode (optional)
        :param digital_pin: GPIO pin number for digital input, native mode (optional)
        :param i2c: Initialized I2C object for easyC mode (optional, auto-detected on ESP32)
        :param address: I2C address for easyC mode, default 0x30, selectable 0x30-0x37
        """
        if analog_pin is not None:
            # Native mode - use ADC and optional digital pin directly
            self.native = True
            self._analogPin = ADC(Pin(analog_pin))
            if uname().sysname in ("esp32", "Soldered Dasduino CONNECTPLUS"):
                self._analogPin.atten(ADC.ATTN_11DB)
                self._adcMax = ADC_MAX_ESP32
            else:
                self._adcMax = ADC_MAX_OTHER
            if digital_pin is not None:
                self._digitalPin = Pin(digital_pin, Pin.IN)
            else:
                self._digitalPin = None
        else:
            # easyC / I2C mode - sensor board has onboard ATtiny with 10-bit ADC
            self.native = False
            self._adcMax = ADC_MAX_OTHER
            self._digitalPin = None
            if i2c is not None:
                self.i2c = i2c
            else:
                if uname().sysname in (
                    "esp32",
                    "esp8266",
                    "Soldered Dasduino CONNECTPLUS",
                ):
                    self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
                else:
                    raise Exception("Board not recognized, enter I2C pins manually")
            self.address = address

        self._highPercentage = 100.0
        self._threshold = DEFAULT_THRESHOLD
        self._rawThreshold = int((1.0 - DEFAULT_THRESHOLD / 100.0) * self._adcMax)
        self._ledInverted = False

    def getRawReading(self) -> int:
        """
        Get raw ADC reading from sensor.

        :returns: int, raw ADC value (0 to ADC_MAX)
        """
        if self.native:
            return self._analogPin.read()
        else:
            try:
                data = self.i2c.readfrom(self.address, 2)
                return (data[1] << 8) | data[0]
            except OSError as e:
                raise Exception("I2C read error: {}".format(e))

    def getResistance(self) -> float:
        """
        Calculate sensor resistance in ohms using 10kOhm pull-up divider formula.
        Note: meaningful in native mode only, assumes pull-up resistor circuit.

        :returns: float, resistance in ohms
        """
        raw = self.getRawReading()
        if raw >= self._adcMax:
            return float("inf")
        if raw == 0:
            return 0.0
        return RES * (raw / float(self._adcMax - raw))

    def getValue(self) -> float:
        """
        Get sensor reading as percentage (0.0-100.0%).
        Higher value means more detected: more rain, more moisture, more light, more heat.

        :returns: float, percentage 0.0-100.0
        """
        raw = self.getRawReading()
        pct = (self._adcMax - raw) / float(self._adcMax) * 100.0
        return min(100.0, pct / self._highPercentage * 100.0)

    def setThreshold(self, threshold: float) -> bool:
        """
        Set detection threshold as percentage.

        :param threshold: float, threshold percentage 0.0-100.0
        :returns: bool, True on success, False if out of range
        """
        if threshold < 0.0 or threshold > 100.0:
            return False
        self._threshold = threshold
        self._rawThreshold = int((1.0 - threshold / 100.0) * self._adcMax)
        if not self.native:
            try:
                raw = self._rawThreshold
                self.i2c.writeto(
                    self.address,
                    bytes([CMD_SET_THRESHOLD, (raw >> 8) & 0xFF, raw & 0xFF]),
                )
            except OSError as e:
                raise Exception("I2C write error: {}".format(e))
        return True

    def getThreshold(self) -> float:
        """
        Get current detection threshold as percentage.

        :returns: float, threshold percentage
        """
        return self._threshold

    def setRawThreshold(self, raw_value: int) -> bool:
        """
        Set detection threshold as raw ADC value.

        :param raw_value: int, raw ADC threshold 0 to ADC_MAX
        :returns: bool, True on success, False if out of range
        """
        if raw_value < 0 or raw_value > self._adcMax:
            return False
        self._rawThreshold = raw_value
        self._threshold = (1.0 - raw_value / float(self._adcMax)) * 100.0
        if not self.native:
            try:
                self.i2c.writeto(
                    self.address,
                    bytes(
                        [CMD_SET_THRESHOLD, (raw_value >> 8) & 0xFF, raw_value & 0xFF]
                    ),
                )
            except OSError as e:
                raise Exception("I2C write error: {}".format(e))
        return True

    def getRawThreshold(self) -> int:
        """
        Get current detection threshold as raw ADC value.

        :returns: int, raw ADC threshold
        """
        return self._rawThreshold

    def invertLED(self, invert: bool) -> None:
        """
        Invert onboard LED behavior.
        Default: LED turns on when reading exceeds threshold.
        Inverted: LED turns off when reading exceeds threshold.
        Note: Only effective in easyC I2C mode, LED is controlled by onboard ATtiny.

        :param invert: bool, True to invert LED behavior
        """
        self._ledInverted = invert
        if not self.native:
            try:
                self.i2c.writeto(self.address, bytes([CMD_SET_LED, 1 if invert else 0]))
            except OSError as e:
                raise Exception("I2C write error: {}".format(e))

    def calibrate(self, high_percentage: float) -> None:
        """
        Calibrate the sensor maximum reading.
        Place sensor in maximum-stimulus condition (fully wet, full light, etc.),
        read getValue(), then pass that value here to rescale to 100%.

        :param high_percentage: float, current getValue() reading to map to 100%
        """
        self._highPercentage = high_percentage
        self._rawThreshold = int(
            (1.0 - self._threshold / 100.0)
            * self._adcMax
            * (self._highPercentage / 100.0)
        )

    def getDigitalPin(self):
        """
        Get the digital Pin object (native mode only).

        :returns: machine.Pin object or None
        """
        return self._digitalPin
