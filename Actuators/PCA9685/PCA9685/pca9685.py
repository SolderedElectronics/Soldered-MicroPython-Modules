# FILE: pca9685.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython driver for PCA9685 16-channel 12-bit PWM/Servo driver
# LAST UPDATED: 2026-07-24

from machine import I2C, Pin
from os import uname
from utime import sleep_ms, sleep_us

# Register addresses
_MODE1 = const(0x00)
_MODE2 = const(0x01)
_LED0_ON_L = const(0x06)
_PRESCALE = const(0xFE)

# MODE1 bits
_MODE1_RESTART = const(0x80)
_MODE1_AI = const(0x20)
_MODE1_SLEEP = const(0x10)
_MODE1_ALLCALL = const(0x01)

# MODE2 bits
_MODE2_OUTDRV = const(0x04)

PCA9685_NUM_CHANNELS = 16
PCA9685_DEFAULT_ADDRESS = 0x40
PCA9685_OSC_FREQ = 25000000.0


class PCA9685:
    """MicroPython driver for PCA9685 16-channel 12-bit PWM/Servo driver (I2C)."""

    def __init__(self, i2c=None, address=PCA9685_DEFAULT_ADDRESS):
        """
        Initialize PCA9685.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: int, I2C address of the board, defaults to 0x40
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self._address = address

        self._pwmFreqHz = 50
        self._servoMinPulseUs = 500
        self._servoMaxPulseUs = 2500
        self._servoMinAngle = 0
        self._servoMaxAngle = 180

        self._writeReg8(_MODE2, _MODE2_OUTDRV)
        self._writeReg8(_MODE1, _MODE1_ALLCALL)
        sleep_ms(5)

        mode1 = self._readReg8(_MODE1)
        mode1 &= ~_MODE1_SLEEP
        self._writeReg8(_MODE1, mode1)
        sleep_ms(5)

        self.setPWMFreq(self._pwmFreqHz)

    def _writeReg8(self, reg, value):
        try:
            self.i2c.writeto_mem(self._address, reg, bytes([value]))
        except OSError as e:
            raise Exception("I2C write error: {}".format(e))

    def _readReg8(self, reg):
        try:
            return self.i2c.readfrom_mem(self._address, reg, 1)[0]
        except OSError as e:
            raise Exception("I2C read error: {}".format(e))

    def setPWMFreq(self, freq: float) -> bool:
        """
        Set the PWM frequency for all 16 channels.

        :param freq: float, desired frequency in Hz, clamped to 24-1526 Hz
        :returns: bool, True on success
        """
        if freq < 24:
            freq = 24
        if freq > 1526:
            freq = 1526

        prescaleVal = (PCA9685_OSC_FREQ / (4096.0 * freq)) - 1.0
        prescale = int(prescaleVal + 0.5)
        if prescale < 3:
            prescale = 3

        self._pwmFreqHz = freq

        oldMode = self._readReg8(_MODE1)
        sleepMode = (oldMode & ~_MODE1_RESTART) | _MODE1_SLEEP
        self._writeReg8(_MODE1, sleepMode)
        self._writeReg8(_PRESCALE, prescale)
        self._writeReg8(_MODE1, oldMode)
        sleep_ms(5)
        self._writeReg8(_MODE1, oldMode | _MODE1_RESTART | _MODE1_AI)

        return True

    def setPWM(self, channel: int, on: int, off: int) -> bool:
        """
        Set raw on/off tick counts for a channel.

        :param channel: int, channel number, 0-15
        :param on: int, tick count (0-4095) at which output turns on
        :param off: int, tick count (0-4095) at which output turns off
        :returns: bool, True on success, False if channel out of range
        """
        if channel >= PCA9685_NUM_CHANNELS:
            return False

        if on > 4095:
            on = 4095
        if off > 4095:
            off = 4095

        reg = _LED0_ON_L + 4 * channel
        try:
            self.i2c.writeto_mem(
                self._address,
                reg,
                bytes([on & 0xFF, on >> 8, off & 0xFF, off >> 8]),
            )
        except OSError as e:
            raise Exception("I2C write error: {}".format(e))

        return True

    def setPin(self, channel: int, value: bool) -> bool:
        """
        Set a channel fully on or fully off, bypassing the PWM counter.

        :param channel: int, channel number, 0-15
        :param value: bool, True to hold output high, False to hold output low
        :returns: bool, True on success, False if channel out of range
        """
        if channel >= PCA9685_NUM_CHANNELS:
            return False

        reg = _LED0_ON_L + 4 * channel
        try:
            if value:
                self.i2c.writeto_mem(self._address, reg, bytes([0x00, 0x10, 0x00, 0x00]))
            else:
                self.i2c.writeto_mem(self._address, reg, bytes([0x00, 0x00, 0x00, 0x10]))
        except OSError as e:
            raise Exception("I2C write error: {}".format(e))

        return True

    def setServoPulseRange(self, minPulseUs: int, maxPulseUs: int):
        """
        Configure the pulse width range used by setServoAngle().

        :param minPulseUs: int, pulse width in microseconds mapped to minAngle
        :param maxPulseUs: int, pulse width in microseconds mapped to maxAngle
        """
        self._servoMinPulseUs = minPulseUs
        self._servoMaxPulseUs = maxPulseUs

    def setServoAngleRange(self, minAngle: float, maxAngle: float):
        """
        Configure the angle range accepted by setServoAngle().

        :param minAngle: float, angle in degrees mapped to minPulseUs
        :param maxAngle: float, angle in degrees mapped to maxPulseUs
        """
        self._servoMinAngle = minAngle
        self._servoMaxAngle = maxAngle

    def setServoAngle(self, channel: int, angle: float) -> bool:
        """
        Drive a hobby servo on the given channel to an angle.
        Assumes setPWMFreq(50) (the default set in __init__()).

        :param channel: int, channel number, 0-15
        :param angle: float, angle in degrees, clamped to the configured angle range
        :returns: bool, True on success, False if channel out of range
        """
        if angle < self._servoMinAngle:
            angle = self._servoMinAngle
        if angle > self._servoMaxAngle:
            angle = self._servoMaxAngle

        t = (angle - self._servoMinAngle) / (self._servoMaxAngle - self._servoMinAngle)
        pulseUs = self._servoMinPulseUs + t * (self._servoMaxPulseUs - self._servoMinPulseUs)

        ticksPerUs = 4096.0 / (1000000.0 / self._pwmFreqHz)
        off = int(pulseUs * ticksPerUs + 0.5)

        return self.setPWM(channel, 0, off)

    def sleep(self):
        """Put the oscillator to sleep (low power, PWM outputs stop)."""
        mode1 = self._readReg8(_MODE1)
        self._writeReg8(_MODE1, mode1 | _MODE1_SLEEP)

    def wake(self):
        """Wake the oscillator back up after sleep()."""
        mode1 = self._readReg8(_MODE1)
        self._writeReg8(_MODE1, mode1 & ~_MODE1_SLEEP)
        sleep_us(500)
