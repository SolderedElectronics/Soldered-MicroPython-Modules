# FILE: ads1x15.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for ADS1015 (12-bit) and ADS1115 (16-bit) 4-channel ADC
# LAST UPDATED: 2026-05-22

from machine import I2C, Pin
from os import uname
import time

ADS1X15_DEFAULT_ADDR = 0x48  # ADDR pin → GND; options: 0x48, 0x49, 0x4A, 0x4B

# Register addresses
ADS1X15_REG_CONVERT        = 0x00
ADS1X15_REG_CONFIG         = 0x01
ADS1X15_REG_LOW_THRESHOLD  = 0x02
ADS1X15_REG_HIGH_THRESHOLD = 0x03

# Bit 15 — OS
ADS1X15_OS_START_SINGLE = 0x8000
ADS1X15_OS_NOT_BUSY     = 0x8000

# Bits 14:12 — MUX
ADS1X15_MUX_DIFF_0_1 = 0x0000  # AIN0(+) vs AIN1(-)
ADS1X15_MUX_DIFF_0_3 = 0x1000  # AIN0(+) vs AIN3(-)
ADS1X15_MUX_DIFF_1_3 = 0x2000  # AIN1(+) vs AIN3(-)
ADS1X15_MUX_DIFF_2_3 = 0x3000  # AIN2(+) vs AIN3(-)

# Bits 11:9 — PGA
ADS1X15_PGA_6_144V = 0x0000  # ±6.144 V (default)
ADS1X15_PGA_4_096V = 0x0200  # ±4.096 V
ADS1X15_PGA_2_048V = 0x0400  # ±2.048 V
ADS1X15_PGA_1_024V = 0x0600  # ±1.024 V
ADS1X15_PGA_0_512V = 0x0800  # ±0.512 V
ADS1X15_PGA_0_256V = 0x0A00  # ±0.256 V

# Bit 8 — mode
ADS1X15_MODE_CONTINUOUS = 0x0000
ADS1X15_MODE_SINGLE     = 0x0100  # default

# Bits 7:5 — data rate index (0=slowest … 7=fastest, 4=default)
# ADS1015: 0=128, 1=250, 2=490, 3=920, 4=1600, 5=2400, 6=3300, 7=3300 SPS
# ADS1115: 0=8,   1=16,  2=32,  3=64,  4=128,  5=250,  6=475,  7=860  SPS

# Bit 4 — comparator mode
ADS1X15_COMP_MODE_TRADITIONAL = 0x0000  # default
ADS1X15_COMP_MODE_WINDOW      = 0x0010

# Bit 3 — comparator polarity
ADS1X15_COMP_POL_ACTIV_LOW  = 0x0000  # default
ADS1X15_COMP_POL_ACTIV_HIGH = 0x0008

# Bit 2 — comparator latch
ADS1X15_COMP_NON_LATCH = 0x0000  # default
ADS1X15_COMP_LATCH     = 0x0004

# Bits 1:0 — comparator queue
ADS1X15_COMP_QUE_1_CONV = 0x0000  # assert after 1 conversion
ADS1X15_COMP_QUE_2_CONV = 0x0001  # assert after 2 conversions
ADS1X15_COMP_QUE_4_CONV = 0x0002  # assert after 4 conversions
ADS1X15_COMP_QUE_NONE   = 0x0003  # disable comparator (default)

ADS1015_CONVERSION_DELAY = 1  # ms
ADS1115_CONVERSION_DELAY = 8  # ms

ADS1X15_OK              =  0
ADS1X15_INVALID_VOLTAGE = -100
ADS1X15_INVALID_GAIN    =  0xFF
ADS1X15_INVALID_MODE    =  0xFE


class ADS1X15:
    """
    Base class for ADS1015 and ADS1115. Do not instantiate directly.
    """

    def __init__(self, i2c=None, address=ADS1X15_DEFAULT_ADDR):
        """
        :param i2c:     Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address (0x48–0x4B, set by ADDR pin strapping)
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
        self._err    = ADS1X15_OK
        self._reset()

    # -------------------------------------------------------------------------
    # Init
    # -------------------------------------------------------------------------

    def begin(self):
        """
        Verify device is reachable on the I2C bus.

        :return: True if device responds, False otherwise
        """
        if self.address < 0x48 or self.address > 0x4B:
            return False
        try:
            self.i2c.readfrom(self.address, 1)
            return True
        except:
            return False

    def _reset(self):
        """Reset config fields to safe defaults."""
        self.setGain(0)      # ±6.144 V — widest, safest range
        self.setMode(1)      # single-shot
        self.setDataRate(4)  # mid-speed default
        self._compMode       = 0
        self._compPol        = 0  # active low
        self._compLatch      = 0  # non-latching
        self._compQueConvert = 3  # comparator disabled

    # -------------------------------------------------------------------------
    # Gain
    # -------------------------------------------------------------------------

    def setGain(self, gain=0):
        """
        Set PGA gain. Invalid values fall back to 0 (safest/widest range).

        :param gain: 0=±6.144V, 1=±4.096V, 2=±2.048V, 4=±1.024V, 8=±0.512V, 16=±0.256V
        """
        _map = {
            0:  ADS1X15_PGA_6_144V,
            1:  ADS1X15_PGA_4_096V,
            2:  ADS1X15_PGA_2_048V,
            4:  ADS1X15_PGA_1_024V,
            8:  ADS1X15_PGA_0_512V,
            16: ADS1X15_PGA_0_256V,
        }
        self._gain = _map.get(gain, ADS1X15_PGA_6_144V)

    def getGain(self):
        """
        Get current gain setting.

        :return: Gain value (0/1/2/4/8/16), or ADS1X15_INVALID_GAIN on error
        """
        _map = {
            ADS1X15_PGA_6_144V: 0,
            ADS1X15_PGA_4_096V: 1,
            ADS1X15_PGA_2_048V: 2,
            ADS1X15_PGA_1_024V: 4,
            ADS1X15_PGA_0_512V: 8,
            ADS1X15_PGA_0_256V: 16,
        }
        val = _map.get(self._gain)
        if val is None:
            self._err = ADS1X15_INVALID_GAIN
            return ADS1X15_INVALID_GAIN
        return val

    def getMaxVoltage(self):
        """
        Get full-scale voltage for the current gain setting.

        :return: Full-scale voltage in Volts, or ADS1X15_INVALID_VOLTAGE on error
        """
        _map = {
            ADS1X15_PGA_6_144V: 6.144,
            ADS1X15_PGA_4_096V: 4.096,
            ADS1X15_PGA_2_048V: 2.048,
            ADS1X15_PGA_1_024V: 1.024,
            ADS1X15_PGA_0_512V: 0.512,
            ADS1X15_PGA_0_256V: 0.256,
        }
        val = _map.get(self._gain)
        if val is None:
            self._err = ADS1X15_INVALID_VOLTAGE
            return ADS1X15_INVALID_VOLTAGE
        return val

    def toVoltage(self, raw=1):
        """
        Convert a raw ADC value to Volts.

        :param raw: Signed raw value from readADC() or getValue()
        :return: Voltage in Volts
        """
        if raw == 0:
            return 0.0
        volts = self.getMaxVoltage()
        if volts < 0:
            return volts
        volts *= raw
        # ADS1115: 15-bit mantissa (32767); ADS1015: 11-bit mantissa (2047)
        volts /= 32767.0 if self._bitShift == 0 else 2047.0
        return volts

    # -------------------------------------------------------------------------
    # Mode
    # -------------------------------------------------------------------------

    def setMode(self, mode=1):
        """
        Set conversion mode.

        :param mode: 0 = continuous, 1 = single-shot (default)
        """
        self._mode = ADS1X15_MODE_CONTINUOUS if mode == 0 else ADS1X15_MODE_SINGLE

    def getMode(self):
        """
        Get conversion mode.

        :return: 0 = continuous, 1 = single-shot, ADS1X15_INVALID_MODE on error
        """
        if self._mode == ADS1X15_MODE_CONTINUOUS:
            return 0
        if self._mode == ADS1X15_MODE_SINGLE:
            return 1
        self._err = ADS1X15_INVALID_MODE
        return ADS1X15_INVALID_MODE

    # -------------------------------------------------------------------------
    # Data rate
    # -------------------------------------------------------------------------

    def setDataRate(self, rate=4):
        """
        Set data rate index (0=slowest … 7=fastest, 4=default). Invalid → 4.
        Actual SPS differs between ADS1015 and ADS1115 — see module constants.

        :param rate: 0–7
        """
        self._datarate = (rate if rate <= 7 else 4) << 5

    def getDataRate(self):
        """
        Get current data rate index.

        :return: 0–7
        """
        return (self._datarate >> 5) & 0x07

    # -------------------------------------------------------------------------
    # Single-ended reads (blocking)
    # -------------------------------------------------------------------------

    def readADC(self, pin):
        """
        Read one single-ended channel, blocking until conversion completes.

        :param pin: Channel 0–3
        :return: Signed raw ADC value, or 0 for invalid pin
        """
        if pin >= self._maxPorts:
            return 0
        return self._readADC((4 + pin) << 12)

    # -------------------------------------------------------------------------
    # Differential reads (blocking)
    # -------------------------------------------------------------------------

    def readADC_Differential_0_1(self):
        """Read AIN0(+) vs AIN1(-) hardware differential (blocking)."""
        return self._readADC(ADS1X15_MUX_DIFF_0_1)

    def readADC_Differential_0_3(self):
        """Read AIN0(+) vs AIN3(-) hardware differential (blocking)."""
        return self._readADC(ADS1X15_MUX_DIFF_0_3)

    def readADC_Differential_1_3(self):
        """Read AIN1(+) vs AIN3(-) hardware differential (blocking)."""
        return self._readADC(ADS1X15_MUX_DIFF_1_3)

    def readADC_Differential_2_3(self):
        """Read AIN2(+) vs AIN3(-) hardware differential (blocking)."""
        return self._readADC(ADS1X15_MUX_DIFF_2_3)

    def readADC_Differential_0_2(self):
        """
        AIN0 vs AIN2 differential via two single-ended reads (not hardware differential).
        Not usable in async mode.
        """
        return self.readADC(2) - self.readADC(0)

    def readADC_Differential_1_2(self):
        """
        AIN1 vs AIN2 differential via two single-ended reads (not hardware differential).
        Not usable in async mode.
        """
        return self.readADC(2) - self.readADC(1)

    # -------------------------------------------------------------------------
    # Async interface — requestADC → isBusy/isReady → getValue
    # -------------------------------------------------------------------------

    def requestADC(self, pin):
        """
        Start a non-blocking single-ended conversion. Poll isBusy() / isReady(),
        then call getValue() for the result.

        :param pin: Channel 0–3
        """
        if pin >= self._maxPorts:
            return
        self._requestADC((4 + pin) << 12)

    def requestADC_Differential_0_1(self):
        """Start non-blocking AIN0(+) vs AIN1(-) differential conversion."""
        self._requestADC(ADS1X15_MUX_DIFF_0_1)

    def requestADC_Differential_0_3(self):
        """Start non-blocking AIN0(+) vs AIN3(-) differential conversion."""
        self._requestADC(ADS1X15_MUX_DIFF_0_3)

    def requestADC_Differential_1_3(self):
        """Start non-blocking AIN1(+) vs AIN3(-) differential conversion."""
        self._requestADC(ADS1X15_MUX_DIFF_1_3)

    def requestADC_Differential_2_3(self):
        """Start non-blocking AIN2(+) vs AIN3(-) differential conversion."""
        self._requestADC(ADS1X15_MUX_DIFF_2_3)

    def isBusy(self):
        """
        Check if a conversion is in progress.

        :return: True while converting, False when result is ready
        """
        return (self._readRegister(ADS1X15_REG_CONFIG) & ADS1X15_OS_NOT_BUSY) == 0

    def isReady(self):
        """
        Check if conversion result is ready.

        :return: True if result ready
        """
        return not self.isBusy()

    def getValue(self):
        """
        Read the conversion register. Call after isBusy() returns False.

        :return: Signed raw ADC value (12-bit for ADS1015, 16-bit for ADS1115)
        """
        raw = self._readRegister(ADS1X15_REG_CONVERT)
        # Sign-extend uint16 → signed int
        if raw >= 0x8000:
            raw -= 0x10000
        if self._bitShift:
            raw >>= self._bitShift  # arithmetic right-shift preserves sign in Python
        return raw

    def getLastValue(self):
        """Alias for getValue()."""
        return self.getValue()

    # -------------------------------------------------------------------------
    # Comparator
    # -------------------------------------------------------------------------

    def setComparatorMode(self, mode):
        """
        Set comparator mode.

        :param mode: 0 = traditional (> high → on, < low → off),
                     1 = window (> high or < low → on)
        """
        self._compMode = 0 if mode == 0 else 1

    def getComparatorMode(self):
        """Get comparator mode (0=traditional, 1=window)."""
        return self._compMode

    def setComparatorPolarity(self, pol):
        """
        Set ALERT/RDY pin polarity.

        :param pol: 0 = active low (default), 1 = active high
        """
        self._compPol = 0 if pol == 0 else 1

    def getComparatorPolarity(self):
        """Get comparator polarity (0=active low, 1=active high)."""
        return self._compPol

    def setComparatorLatch(self, latch):
        """
        Set comparator latch behavior.

        :param latch: 0 = non-latching (default), 1 = latching
        """
        self._compLatch = 0 if latch == 0 else 1

    def getComparatorLatch(self):
        """Get comparator latch (0=non-latching, 1=latching)."""
        return self._compLatch

    def setComparatorQueConvert(self, mode):
        """
        Set how many conversions trigger the ALERT/RDY pin.

        :param mode: 0=after 1, 1=after 2, 2=after 4, 3=disable (default)
        """
        self._compQueConvert = mode if mode < 3 else 3

    def getComparatorQueConvert(self):
        """Get comparator queue setting (0–3)."""
        return self._compQueConvert

    def setComparatorThresholdLow(self, lo):
        """
        Set low threshold for the comparator.

        :param lo: Signed 16-bit threshold value
        """
        self._writeRegister(ADS1X15_REG_LOW_THRESHOLD, lo & 0xFFFF)

    def getComparatorThresholdLow(self):
        """
        Get low threshold register value.

        :return: Signed 16-bit threshold
        """
        raw = self._readRegister(ADS1X15_REG_LOW_THRESHOLD)
        return raw if raw < 0x8000 else raw - 0x10000

    def setComparatorThresholdHigh(self, hi):
        """
        Set high threshold for the comparator.

        :param hi: Signed 16-bit threshold value
        """
        self._writeRegister(ADS1X15_REG_HIGH_THRESHOLD, hi & 0xFFFF)

    def getComparatorThresholdHigh(self):
        """
        Get high threshold register value.

        :return: Signed 16-bit threshold
        """
        raw = self._readRegister(ADS1X15_REG_HIGH_THRESHOLD)
        return raw if raw < 0x8000 else raw - 0x10000

    # -------------------------------------------------------------------------
    # Error
    # -------------------------------------------------------------------------

    def getError(self):
        """
        Get and clear the last error code.

        :return: ADS1X15_OK, ADS1X15_INVALID_GAIN, ADS1X15_INVALID_VOLTAGE, or ADS1X15_INVALID_MODE
        """
        err = self._err
        self._err = ADS1X15_OK
        return err

    # -------------------------------------------------------------------------
    # Private
    # -------------------------------------------------------------------------

    def _readADC(self, readmode):
        """Blocking conversion: write config, wait, return signed raw value."""
        self._requestADC(readmode)
        if self._mode == ADS1X15_MODE_SINGLE:
            while self.isBusy():
                time.sleep_ms(1)
        else:
            time.sleep_ms(self._conversionDelay)
        return self.getValue()

    def _requestADC(self, readmode):
        """Write config register to trigger one conversion."""
        config  = ADS1X15_OS_START_SINGLE
        config |= readmode
        config |= self._gain
        config |= self._mode
        config |= self._datarate
        config |= ADS1X15_COMP_MODE_WINDOW    if self._compMode  else ADS1X15_COMP_MODE_TRADITIONAL
        config |= ADS1X15_COMP_POL_ACTIV_HIGH if self._compPol   else ADS1X15_COMP_POL_ACTIV_LOW
        config |= ADS1X15_COMP_LATCH          if self._compLatch  else ADS1X15_COMP_NON_LATCH
        config |= self._compQueConvert
        self._writeRegister(ADS1X15_REG_CONFIG, config)

    def _writeRegister(self, reg, value):
        """Write 16-bit value to a register (MSB first)."""
        try:
            self.i2c.writeto(self.address, bytes([reg, (value >> 8) & 0xFF, value & 0xFF]))
            return True
        except:
            return False

    def _readRegister(self, reg):
        """Write register address, read back 2-byte big-endian value."""
        try:
            self.i2c.writeto(self.address, bytes([reg]))
            data = self.i2c.readfrom(self.address, 2)
            return (data[0] << 8) | data[1]
        except:
            return 0x0000


class ADS1015(ADS1X15):
    """
    12-bit, 4-channel ADC with PGA and comparator.
    Conversion delay: 1 ms. Data rates: 128–3300 SPS.
    """

    def __init__(self, i2c=None, address=ADS1X15_DEFAULT_ADDR):
        """
        :param i2c:     Initialized I2C object (optional)
        :param address: I2C address (default 0x48)
        """
        self._conversionDelay = ADS1015_CONVERSION_DELAY
        self._bitShift        = 4  # 12-bit result stored in bits 15:4 of the conversion register
        self._maxPorts        = 4
        super().__init__(i2c, address)


class ADS1115(ADS1X15):
    """
    16-bit, 4-channel ADC with PGA and comparator.
    Conversion delay: 8 ms. Data rates: 8–860 SPS.
    """

    def __init__(self, i2c=None, address=ADS1X15_DEFAULT_ADDR):
        """
        :param i2c:     Initialized I2C object (optional)
        :param address: I2C address (default 0x48)
        """
        self._conversionDelay = ADS1115_CONVERSION_DELAY
        self._bitShift        = 0  # full 16-bit result
        self._maxPorts        = 4
        super().__init__(i2c, address)
