# FILE: as5600.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython driver for AS5600 magnetic rotation angle sensor
# LAST UPDATED: 2026-07-02

from machine import ADC, Pin, I2C
from os import uname
from math import pi
import time

# Default I2C address (fixed for AS5600)
AS5600_I2C_ADDR = 0x36

# ADC Resolution (native mode)
ADC_MAX_ESP32 = 4095  # ESP32 12-bit ADC
ADC_MAX_OTHER = 1023  # 10-bit ADC

# Configuration registers
_REG_ZMCO = 0x00
_REG_ZPOS = 0x01  # + 0x02
_REG_MPOS = 0x03  # + 0x04
_REG_MANG = 0x05  # + 0x06
_REG_CONF = 0x07  # + 0x08

# Configuration bit masks (byte-level, second byte of CONF pair)
_CONF_POWER_MODE = 0x03
_CONF_HYSTERESIS = 0x0C
_CONF_OUTPUT_MODE = 0x30
_CONF_PWM_FREQUENCY = 0xC0
# Configuration bit masks (first byte of CONF pair)
_CONF_SLOW_FILTER = 0x03
_CONF_FAST_FILTER = 0x1C
_CONF_WATCH_DOG = 0x20

# Output registers
_REG_RAW_ANGLE = 0x0C  # + 0x0D
_REG_ANGLE = 0x0E  # + 0x0F

# Status registers
_REG_STATUS = 0x0B
_REG_AGC = 0x1A
_REG_MAGNITUDE = 0x1B  # + 0x1C

# Status bits
STATUS_MAGNET_HIGH = 0x08
STATUS_MAGNET_LOW = 0x10
STATUS_MAGNET_DETECT = 0x20

# setDirection
DIR_CLOCKWISE = 0
DIR_COUNTERCLOCKWISE = 1

# setOutputMode
OUTMODE_ANALOG_100 = 0
OUTMODE_ANALOG_90 = 1
OUTMODE_PWM = 2

# setPowerMode
POWERMODE_NOMINAL = 0
POWERMODE_LOW1 = 1
POWERMODE_LOW2 = 2
POWERMODE_LOW3 = 3

# setPWMFrequency
PWM_115 = 0
PWM_230 = 1
PWM_460 = 2
PWM_920 = 3

# setHysteresis
HYST_OFF = 0
HYST_LSB1 = 1
HYST_LSB2 = 2
HYST_LSB3 = 3

# setSlowFilter
SLOW_FILT_16X = 0
SLOW_FILT_8X = 1
SLOW_FILT_4X = 2
SLOW_FILT_2X = 3

# setFastFilter
FAST_FILT_NONE = 0
FAST_FILT_LSB6 = 1
FAST_FILT_LSB7 = 2
FAST_FILT_LSB9 = 3
FAST_FILT_LSB18 = 4
FAST_FILT_LSB21 = 5
FAST_FILT_LSB24 = 6
FAST_FILT_LSB10 = 7

# setWatchDog
WATCHDOG_OFF = 0
WATCHDOG_ON = 1

# getAngularSpeed modes
MODE_DEGREES = 0
MODE_RADIANS = 1
MODE_RPM = 2
MODE_RPS = 3

# Conversion constants
RAW_TO_DEGREES = 360.0 / 4096
DEGREES_TO_RAW = 4096 / 360.0
RAW_TO_RADIANS = (pi * 2.0) / 4096
RAW_TO_RPM = 60.0 / 4096
RAW_TO_RPS = 1.0 / 4096


class AS5600:
    """
    MicroPython driver for the AS5600 magnetic rotation angle sensor.
    Works in native mode (ADC read of OUT pin, factory default 0-100% analog output)
    or I2C mode (full register access). An optional hardware direction pin is
    supported in both modes; without one, direction is applied in software.
    """

    def __init__(self, analog_pin=None, direction_pin=None, i2c=None, address=AS5600_I2C_ADDR):
        """
        Initialize the AS5600.
        Pass analog_pin for native mode, or leave empty for I2C mode.

        :param analog_pin: GPIO pin number for analog input from OUT pin, native mode (optional)
        :param direction_pin: GPIO pin number wired to sensor DIR pin (optional). If not given,
            direction is applied in software instead of driving the sensor's hardware DIR pin.
        :param i2c: Initialized I2C object for I2C mode (optional, auto-detected on ESP32)
        :param address: I2C address, default 0x36 (fixed for AS5600)
        """
        self._directionPin = None
        self._direction = DIR_CLOCKWISE
        if direction_pin is not None:
            self._directionPin = Pin(direction_pin, Pin.OUT)
        self.setDirection(DIR_CLOCKWISE)

        if analog_pin is not None:
            # Native mode - read OUT pin via ADC
            self.native = True
            self._analogPin = ADC(Pin(analog_pin))
            if uname().sysname in ("esp32", "Soldered Dasduino CONNECTPLUS"):
                self._analogPin.atten(ADC.ATTN_11DB)
                self._adcMax = ADC_MAX_ESP32
            else:
                self._adcMax = ADC_MAX_OTHER
        else:
            # I2C mode - full register access
            self.native = False
            if i2c is not None:
                self.i2c = i2c
            else:
                if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                    self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
                else:
                    raise Exception("Board not recognized, enter I2C pins manually")
            self.address = address
            if not self.isConnected():
                raise Exception("AS5600 not found! Check wiring.")

        self._offset = 0

        # for getAngularSpeed()
        self._lastMeasurement = 0
        self._lastAngle = 0
        self._lastReadAngle = 0

        # for getCumulativePosition()
        self._position = 0
        self._lastPosition = 0

    def isConnected(self):
        """
        Check whether the sensor responds on the I2C bus. Always True in native mode.

        :returns: bool, True if sensor acknowledges on I2C (or native mode)
        """
        if self.native:
            return True
        try:
            self.i2c.writeto(self.address, b"")
            return True
        except OSError:
            return False

    def getAddress(self):
        """
        Get the I2C address in use.

        :returns: int, I2C address
        """
        self._requireI2C()
        return self.address

    #####################################################
    #
    #  CONFIGURATION REGISTERS + direction pin
    #
    def setDirection(self, direction=DIR_CLOCKWISE):
        """
        Set rotation direction. Drives the hardware DIR pin if one was given at init,
        otherwise applied in software when reading the angle.

        :param direction: DIR_CLOCKWISE or DIR_COUNTERCLOCKWISE
        """
        self._direction = direction
        if self._directionPin is not None:
            self._directionPin.value(direction)

    def getDirection(self):
        """
        :returns: int, DIR_CLOCKWISE or DIR_COUNTERCLOCKWISE
        """
        if self._directionPin is not None:
            self._direction = self._directionPin.value()
        return self._direction

    def getZMCO(self):
        """
        :returns: int, number of times ZPOS/MPOS have been burned (max 3)
        """
        self._requireI2C()
        return self._readReg(_REG_ZMCO)

    def setZPosition(self, value):
        """
        :param value: int, 0-4095
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if value > 0x0FFF:
            return False
        self._writeReg2(_REG_ZPOS, value)
        return True

    def getZPosition(self):
        """
        :returns: int, 0-4095
        """
        self._requireI2C()
        return self._readReg2(_REG_ZPOS) & 0x0FFF

    def setMPosition(self, value):
        """
        :param value: int, 0-4095
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if value > 0x0FFF:
            return False
        self._writeReg2(_REG_MPOS, value)
        return True

    def getMPosition(self):
        """
        :returns: int, 0-4095
        """
        self._requireI2C()
        return self._readReg2(_REG_MPOS) & 0x0FFF

    def setMaxAngle(self, value):
        """
        :param value: int, 0-4095
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if value > 0x0FFF:
            return False
        self._writeReg2(_REG_MANG, value)
        return True

    def getMaxAngle(self):
        """
        :returns: int, 0-4095
        """
        self._requireI2C()
        return self._readReg2(_REG_MANG) & 0x0FFF

    #####################################################
    #
    #  CONFIGURATION
    #
    def setConfiguration(self, value):
        """
        Access the whole configuration register. Check datasheet for bit fields.

        :param value: int, 0-0x3FFF
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if value > 0x3FFF:
            return False
        self._writeReg2(_REG_CONF, value)
        return True

    def getConfiguration(self):
        """
        :returns: int, 0-0x3FFF
        """
        self._requireI2C()
        return self._readReg2(_REG_CONF) & 0x3FFF

    def setPowerMode(self, power_mode):
        """
        :param power_mode: POWERMODE_NOMINAL, POWERMODE_LOW1/2/3
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if power_mode > 3:
            return False
        value = self._readReg(_REG_CONF + 1)
        value &= ~_CONF_POWER_MODE
        value |= power_mode
        self._writeReg(_REG_CONF + 1, value)
        return True

    def getPowerMode(self):
        """
        :returns: int, current power mode
        """
        self._requireI2C()
        return self._readReg(_REG_CONF + 1) & 0x03

    def setHysteresis(self, hysteresis):
        """
        Suppresses noise when the magnet is not moving.

        :param hysteresis: HYST_OFF, HYST_LSB1, HYST_LSB2, HYST_LSB3
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if hysteresis > 3:
            return False
        value = self._readReg(_REG_CONF + 1)
        value &= ~_CONF_HYSTERESIS
        value |= hysteresis << 2
        self._writeReg(_REG_CONF + 1, value)
        return True

    def getHysteresis(self):
        """
        :returns: int, current hysteresis setting
        """
        self._requireI2C()
        return (self._readReg(_REG_CONF + 1) >> 2) & 0x03

    def setOutputMode(self, output_mode):
        """
        :param output_mode: OUTMODE_ANALOG_100, OUTMODE_ANALOG_90, OUTMODE_PWM
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if output_mode > 2:
            return False
        value = self._readReg(_REG_CONF + 1)
        value &= ~_CONF_OUTPUT_MODE
        value |= output_mode << 4
        self._writeReg(_REG_CONF + 1, value)
        return True

    def getOutputMode(self):
        """
        :returns: int, current output mode
        """
        self._requireI2C()
        return (self._readReg(_REG_CONF + 1) >> 4) & 0x03

    def setPWMFrequency(self, pwm_freq):
        """
        :param pwm_freq: PWM_115, PWM_230, PWM_460, PWM_920
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if pwm_freq > 3:
            return False
        value = self._readReg(_REG_CONF + 1)
        value &= ~_CONF_PWM_FREQUENCY
        value |= pwm_freq << 6
        self._writeReg(_REG_CONF + 1, value)
        return True

    def getPWMFrequency(self):
        """
        :returns: int, current PWM frequency setting
        """
        self._requireI2C()
        return (self._readReg(_REG_CONF + 1) >> 6) & 0x03

    def setSlowFilter(self, mask):
        """
        :param mask: SLOW_FILT_16X, SLOW_FILT_8X, SLOW_FILT_4X, SLOW_FILT_2X
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if mask > 3:
            return False
        value = self._readReg(_REG_CONF)
        value &= ~_CONF_SLOW_FILTER
        value |= mask
        self._writeReg(_REG_CONF, value)
        return True

    def getSlowFilter(self):
        """
        :returns: int, current slow filter setting
        """
        self._requireI2C()
        return self._readReg(_REG_CONF) & 0x03

    def setFastFilter(self, mask):
        """
        :param mask: FAST_FILT_NONE, FAST_FILT_LSB6/7/9/18/21/24/10
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if mask > 7:
            return False
        value = self._readReg(_REG_CONF)
        value &= ~_CONF_FAST_FILTER
        value |= mask << 2
        self._writeReg(_REG_CONF, value)
        return True

    def getFastFilter(self):
        """
        :returns: int, current fast filter setting
        """
        self._requireI2C()
        return (self._readReg(_REG_CONF) >> 2) & 0x07

    def setWatchDog(self, mask):
        """
        :param mask: WATCHDOG_OFF or WATCHDOG_ON (auto low power mode)
        :returns: bool, True on success, False if out of range
        """
        self._requireI2C()
        if mask > 1:
            return False
        value = self._readReg(_REG_CONF)
        value &= ~_CONF_WATCH_DOG
        value |= mask << 5
        self._writeReg(_REG_CONF, value)
        return True

    def getWatchDog(self):
        """
        :returns: int, WATCHDOG_OFF or WATCHDOG_ON
        """
        self._requireI2C()
        return (self._readReg(_REG_CONF) >> 5) & 0x01

    #####################################################
    #
    #  OUTPUT REGISTERS
    #
    def rawAngle(self):
        """
        Read the raw angle, unaffected by ZPOS/MPOS scaling.

        :returns: int, 0-4095
        """
        value = self._readAngleRaw(_REG_RAW_ANGLE)
        if self._offset > 0:
            value += self._offset
        value &= 0x0FFF
        if self._directionPin is None and self._direction == DIR_COUNTERCLOCKWISE:
            value = (4096 - value) & 0x0FFF
        return value

    def readAngle(self):
        """
        Read the scaled angle (affected by ZPOS/MPOS/MANG).

        :returns: int, 0-4095
        """
        value = self._readAngleRaw(_REG_ANGLE)
        if self._offset > 0:
            value += self._offset
        value &= 0x0FFF
        if self._directionPin is None and self._direction == DIR_COUNTERCLOCKWISE:
            # mask needed for value == 0
            value = (4096 - value) & 0x0FFF
        self._lastReadAngle = value
        return value

    def _readAngleRaw(self, reg):
        if self.native:
            reading = self._analogPin.read()
            return int(reading / self._adcMax * 4096) & 0x0FFF
        return self._readReg2(reg)

    def setOffset(self, degrees):
        """
        Set a software angle offset. Expect loss of precision.

        :param degrees: float, -36000..36000 (preferred -359.99..359.99)
        :returns: bool, True on success, False if abs(degrees) > 36000
        """
        if abs(degrees) > 36000:
            return False
        neg = degrees < 0
        if neg:
            degrees = -degrees
        offset = round(degrees * DEGREES_TO_RAW)
        offset &= 0x0FFF
        if neg:
            offset = (4096 - offset) & 0x0FFF
        self._offset = offset
        return True

    def getOffset(self):
        """
        :returns: float, current offset in degrees
        """
        return self._offset * RAW_TO_DEGREES

    def increaseOffset(self, degrees):
        """
        Add to the existing offset.

        :param degrees: float, degrees to add to current offset
        :returns: bool, True on success, False if resulting offset out of range
        """
        return self.setOffset((self._offset * RAW_TO_DEGREES) + degrees)

    #####################################################
    #
    #  STATUS REGISTERS
    #
    def readStatus(self):
        """
        :returns: int, raw status register value
        """
        self._requireI2C()
        return self._readReg(_REG_STATUS)

    def readAGC(self):
        """
        :returns: int, automatic gain control value
        """
        self._requireI2C()
        return self._readReg(_REG_AGC)

    def readMagnitude(self):
        """
        :returns: int, magnitude of the internal CORDIC
        """
        self._requireI2C()
        return self._readReg2(_REG_MAGNITUDE) & 0x0FFF

    def magnetDetected(self):
        """
        :returns: bool, True if magnet is detected
        """
        return bool(self.readStatus() & STATUS_MAGNET_DETECT)

    def magnetTooStrong(self):
        """
        :returns: bool, True if magnet field is too strong
        """
        return bool(self.readStatus() & STATUS_MAGNET_HIGH)

    def magnetTooWeak(self):
        """
        :returns: bool, True if magnet field is too weak
        """
        return bool(self.readStatus() & STATUS_MAGNET_LOW)

    #####################################################
    #
    #  ANGULAR SPEED
    #
    def getAngularSpeed(self, mode=MODE_DEGREES, update=True):
        """
        Approximate angular speed from the last two angle readings.
        Assumes no more than 180 degrees of rotation between calls
        (at least two calls per revolution, four preferred).

        :param mode: MODE_DEGREES, MODE_RADIANS, MODE_RPM, or MODE_RPS
        :param update: bool, if True calls readAngle() first, else uses last known value
        :returns: float, angular speed in the requested unit
        """
        if update:
            self._lastReadAngle = self.readAngle()

        now = time.ticks_us()
        angle = self._lastReadAngle
        delta_t = time.ticks_diff(now, self._lastMeasurement)
        delta_a = angle - self._lastAngle

        if delta_a > 2048:
            delta_a -= 4096
        elif delta_a < -2048:
            delta_a += 4096
        speed = (delta_a * 1e6) / delta_t if delta_t != 0 else 0.0

        self._lastMeasurement = now
        self._lastAngle = angle

        if mode == MODE_RADIANS:
            return speed * RAW_TO_RADIANS
        if mode == MODE_RPM:
            return speed * RAW_TO_RPM
        if mode == MODE_RPS:
            return speed * RAW_TO_RPS
        return speed * RAW_TO_DEGREES

    #####################################################
    #
    #  POSITION cumulative
    #
    def getCumulativePosition(self, update=True):
        """
        Reads the sensor (unless update=False) and updates cumulative position.
        Only accurate if read often enough to catch each rotation crossing.

        :param update: bool, if True calls readAngle() first, else uses last known value
        :returns: int, cumulative position (signed, in raw units)
        """
        if update:
            self._lastReadAngle = self.readAngle()
        value = self._lastReadAngle

        # whole rotation CW? less than half a circle
        if self._lastPosition > 2048 and value < (self._lastPosition - 2048):
            self._position = self._position + 4096 - self._lastPosition + value
        # whole rotation CCW? less than half a circle
        elif value > 2048 and self._lastPosition < (value - 2048):
            self._position = self._position - 4096 - self._lastPosition + value
        else:
            self._position = self._position - self._lastPosition + value
        self._lastPosition = value

        return self._position

    def getRevolutions(self):
        """
        Converts the last cumulative position to whole revolutions.

        :returns: int, whole revolutions
        """
        p = self._position >> 12  # divide by 4096
        if p < 0:
            p += 1  # correct negative values
        return p

    def resetPosition(self, position=0):
        """
        Resets position only, not the internal last-position tracker.

        :param position: int, new position value
        :returns: int, previous position
        """
        old = self._position
        self._position = position
        return old

    def resetCumulativePosition(self, position=0):
        """
        Resets position and the internal last-position tracker.

        :param position: int, new position value
        :returns: int, previous position
        """
        self._lastPosition = self.readAngle()
        old = self._position
        self._position = position
        return old

    #####################################################
    #
    #  PROTECTED
    #
    def _requireI2C(self):
        if self.native:
            raise Exception("Not available in native mode")

    def _readReg(self, reg):
        try:
            return self.i2c.readfrom_mem(self.address, reg, 1)[0]
        except OSError as e:
            raise Exception("I2C read error: {}".format(e))

    def _readReg2(self, reg):
        try:
            data = self.i2c.readfrom_mem(self.address, reg, 2)
        except OSError as e:
            raise Exception("I2C read error: {}".format(e))
        return (data[0] << 8) | data[1]

    def _writeReg(self, reg, value):
        try:
            self.i2c.writeto_mem(self.address, reg, bytes([value]))
        except OSError as e:
            raise Exception("I2C write error: {}".format(e))

    def _writeReg2(self, reg, value):
        try:
            self.i2c.writeto_mem(self.address, reg, bytes([(value >> 8) & 0xFF, value & 0xFF]))
        except OSError as e:
            raise Exception("I2C write error: {}".format(e))
