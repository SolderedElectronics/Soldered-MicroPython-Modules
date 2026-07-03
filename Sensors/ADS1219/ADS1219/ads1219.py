# FILE: ads1219.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the ADS1219 24-bit 4-channel ADC
# LAST UPDATED: 2026-05-19

from machine import I2C, Pin
from os import uname
import time

# Default I2C address (A1=GND, A0=GND). Range 0x40-0x4F depending on A1/A0 pin strapping.
ADS1219_DEFAULT_ADDR = 0x40

# Commands
ADS1219_CMD_RESET = 0x06  # Soft reset — config returns to 0x00
ADS1219_CMD_START_SYNC = 0x08  # Start or restart conversion
ADS1219_CMD_POWERDOWN = 0x02  # Enter power-down mode
ADS1219_CMD_RDATA = 0x10  # Read conversion result (3 bytes, big-endian)

# Register addresses
ADS1219_REG_CFG_WRITE = 0x40  # Write configuration register
ADS1219_REG_CFG_READ = 0x20  # Read configuration register
ADS1219_REG_STATUS = 0x24  # Read status register

###########################
# Mux constants           #
###########################
ADS1219_MUX_DIFF_P0_N1 = 0  # Differential: AINP=AIN0, AINN=AIN1 (default)
ADS1219_MUX_DIFF_P2_N3 = 1  # Differential: AINP=AIN2, AINN=AIN3
ADS1219_MUX_DIFF_P1_N2 = 2  # Differential: AINP=AIN1, AINN=AIN2
ADS1219_MUX_SINGLE_0 = 3  # Single-ended: AINP=AIN0, AINN=AGND
ADS1219_MUX_SINGLE_1 = 4  # Single-ended: AINP=AIN1, AINN=AGND
ADS1219_MUX_SINGLE_2 = 5  # Single-ended: AINP=AIN2, AINN=AGND
ADS1219_MUX_SINGLE_3 = 6  # Single-ended: AINP=AIN3, AINN=AGND
ADS1219_MUX_SHORTED = 7  # Shorted: AINP=AINN=AVDD/2 (offset measurement)

###########################
# Gain constants          #
###########################
ADS1219_GAIN_1 = 0  # Gain = 1, full-scale = VREF (default)
ADS1219_GAIN_4 = 1  # Gain = 4, full-scale = VREF/4

###########################
# Data rate constants     #
###########################
ADS1219_DR_20SPS = 0  # 20 samples per second (default)
ADS1219_DR_90SPS = 1  # 90 samples per second
ADS1219_DR_330SPS = 2  # 330 samples per second
ADS1219_DR_1000SPS = 3  # 1000 samples per second

###########################
# Conversion mode consts  #
###########################
ADS1219_MODE_SINGLE_SHOT = 0  # One conversion per startSync() call (default)
ADS1219_MODE_CONTINUOUS = 1  # Back-to-back conversions until powerDown()

###########################
# Voltage reference consts#
###########################
ADS1219_VREF_INTERNAL = 0  # Internal 2.048V reference (default)
ADS1219_VREF_EXTERNAL = 1  # External reference on REFP/REFN pins


class ADS1219:
    """
    MicroPython class for the TI ADS1219 24-bit 4-channel ADC.
    Communicates over I2C.
    """

    def __init__(self, i2c=None, address=ADS1219_DEFAULT_ADDR):
        """
        Initialize the ADS1219.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address of the device (default 0x40)
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            elif uname().sysname == "esp8266":
                self.i2c = I2C(scl=Pin(5), sda=Pin(4))
            else:
                raise Exception(
                    "Board not recognized, please pass an I2C object manually"
                )

        self.address = address
        self._gain = ADS1219_GAIN_1
        self._result = 0

    # -------------------------------------------------------------------------
    # Initialization and control
    # -------------------------------------------------------------------------

    def begin(self):
        """
        Initialize: soft reset, verify config register reads 0x00.

        :return: True if device found and reset successful, False otherwise
        """
        if not self.reset():
            return False
        time.sleep_ms(1)  # tRSSTA: >100us after reset per datasheet
        cfg = self._readRegister(ADS1219_REG_CFG_READ)
        if cfg is None:
            return False
        return cfg == 0x00

    def reset(self):
        """
        Soft reset. Config register returns to default (0x00).

        :return: True on success
        """
        return self._writeCommand(ADS1219_CMD_RESET)

    def startSync(self):
        """
        Start or restart a conversion.
        Single-shot mode: triggers one conversion.
        Continuous mode: restarts conversion sequence.

        :return: True on success
        """
        return self._writeCommand(ADS1219_CMD_START_SYNC)

    def powerDown(self):
        """
        Enter power-down mode. Stops conversions and powers down analog front-end.

        :return: True on success
        """
        return self._writeCommand(ADS1219_CMD_POWERDOWN)

    # -------------------------------------------------------------------------
    # Conversion
    # -------------------------------------------------------------------------

    def readConversion(self):
        """
        Read 24-bit conversion result from the ADC and store internally.
        Call after dataReady() returns True.

        :return: True on success
        """
        raw = self._readBytes(ADS1219_CMD_RDATA, 3)
        if raw is None:
            return False
        val = (raw[0] << 16) | (raw[1] << 8) | raw[2]
        # Sign-extend 24-bit 2's complement to Python int
        if val & 0x00800000:
            val |= 0xFF000000
            val -= 0x100000000
        self._result = val
        return True

    def getConversionRaw(self):
        """
        Get raw 24-bit signed conversion result (not adjusted for gain).

        :return: Signed integer (24-bit 2's complement, sign-extended)
        """
        return self._result

    def getConversionMillivolts(self, ref_millivolts=2048.0):
        """
        Convert stored result to millivolts.

        :param ref_millivolts: Reference voltage in mV. Use 2048.0 for internal reference,
                               or (REFP - REFN) in mV for external reference.
        :return: Voltage in millivolts, adjusted for gain
        """
        mv = self._result / 8388608.0 * ref_millivolts  # 2^23 = 8388608
        if self._gain == ADS1219_GAIN_4:
            mv /= 4.0
        return mv

    def dataReady(self):
        """
        Check if a conversion result is ready to read.

        :return: True if DRDY flag (bit 7) is set in status register
        """
        status = self._readRegister(ADS1219_REG_STATUS)
        if status is None:
            return False
        return bool(status & 0x80)

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    def setMux(self, mux=ADS1219_MUX_DIFF_P0_N1):
        """
        Configure the input multiplexer.

        :param mux: ADS1219_MUX_* constant (default: differential AIN0/AIN1)
        :return: True on success
        """
        cfg = self._readRegister(ADS1219_REG_CFG_READ)
        if cfg is None:
            return False
        cfg = (cfg & 0x1F) | ((mux & 0x07) << 5)
        return self._writeRegister(ADS1219_REG_CFG_WRITE, cfg)

    def setGain(self, gain=ADS1219_GAIN_1):
        """
        Configure the PGA gain.

        :param gain: ADS1219_GAIN_1 or ADS1219_GAIN_4 (default: 1)
        :return: True on success
        """
        cfg = self._readRegister(ADS1219_REG_CFG_READ)
        if cfg is None:
            return False
        cfg = (cfg & 0xEF) | ((gain & 0x01) << 4)
        self._gain = gain
        return self._writeRegister(ADS1219_REG_CFG_WRITE, cfg)

    def setDataRate(self, rate=ADS1219_DR_20SPS):
        """
        Configure the data rate.

        :param rate: ADS1219_DR_* constant (default: 20 SPS)
        :return: True on success
        """
        cfg = self._readRegister(ADS1219_REG_CFG_READ)
        if cfg is None:
            return False
        cfg = (cfg & 0xF3) | ((rate & 0x03) << 2)
        return self._writeRegister(ADS1219_REG_CFG_WRITE, cfg)

    def setConversionMode(self, mode=ADS1219_MODE_SINGLE_SHOT):
        """
        Configure conversion mode.

        :param mode: ADS1219_MODE_SINGLE_SHOT or ADS1219_MODE_CONTINUOUS (default: single-shot)
        :return: True on success
        """
        cfg = self._readRegister(ADS1219_REG_CFG_READ)
        if cfg is None:
            return False
        cfg = (cfg & 0xFD) | ((mode & 0x01) << 1)
        return self._writeRegister(ADS1219_REG_CFG_WRITE, cfg)

    def setVoltageReference(self, vref=ADS1219_VREF_INTERNAL):
        """
        Configure voltage reference source.

        :param vref: ADS1219_VREF_INTERNAL (2.048V) or ADS1219_VREF_EXTERNAL (default: internal)
        :return: True on success
        """
        cfg = self._readRegister(ADS1219_REG_CFG_READ)
        if cfg is None:
            return False
        cfg = (cfg & 0xFE) | (vref & 0x01)
        return self._writeRegister(ADS1219_REG_CFG_WRITE, cfg)

    def getConfigReg(self):
        """
        Read the full configuration register byte.

        :return: Config register value (int), or None on error
        """
        return self._readRegister(ADS1219_REG_CFG_READ)

    def setConfigReg(self, cfg_byte):
        """
        Write the configuration register directly.
        Also updates internal gain cache used by getConversionMillivolts().

        :param cfg_byte: Register byte value
        :return: True on success
        """
        self._gain = (cfg_byte >> 4) & 0x01
        return self._writeRegister(ADS1219_REG_CFG_WRITE, cfg_byte)

    # -------------------------------------------------------------------------
    # Private: I2C helpers
    # -------------------------------------------------------------------------

    def _writeCommand(self, cmd):
        """
        Send a single-byte command.

        :param cmd: Command byte
        :return: True on success
        """
        try:
            self.i2c.writeto(self.address, bytes([cmd]))
            return True
        except:
            return False

    def _writeRegister(self, reg, data):
        """
        Write a register address followed by one data byte.

        :param reg:  Register address byte
        :param data: Data byte
        :return: True on success
        """
        try:
            self.i2c.writeto(self.address, bytes([reg, data]))
            return True
        except:
            return False

    def _readRegister(self, reg):
        """
        Write register address then read one byte (repeated start).

        :param reg: Register address byte
        :return: Register value (int), or None on error
        """
        try:
            self.i2c.writeto(self.address, bytes([reg]), False)  # repeated start
            data = self.i2c.readfrom(self.address, 1)
            return data[0]
        except:
            return None

    def _readBytes(self, reg, length):
        """
        Write register/command byte then read multiple bytes (repeated start).

        :param reg:    Register/command byte
        :param length: Number of bytes to read
        :return: bytes object, or None on error
        """
        try:
            self.i2c.writeto(self.address, bytes([reg]), False)  # repeated start
            return self.i2c.readfrom(self.address, length)
        except:
            return None
