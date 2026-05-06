# FILE: ina219.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the INA219 Monitor
# LAST UPDATED: 2026-05-06

from machine import I2C, Pin
from os import uname
import math
import time

# Default I2C address
INA219_ADDRESS = 0x40

# Register addresses
INA219_REG_CONFIG      = 0x00
INA219_REG_SHUNTVOLTAGE = 0x01
INA219_REG_BUSVOLTAGE  = 0x02
INA219_REG_POWER       = 0x03
INA219_REG_CURRENT     = 0x04
INA219_REG_CALIBRATION = 0x05

###########################
# Range constants         #
###########################
INA219_RANGE_16V = 0b0  # Bus voltage range 16V
INA219_RANGE_32V = 0b1  # Bus voltage range 32V (default)

###########################
# Gain constants          #
###########################
INA219_GAIN_40MV  = 0b00  # PGA gain ±40mV
INA219_GAIN_80MV  = 0b01  # PGA gain ±80mV
INA219_GAIN_160MV = 0b10  # PGA gain ±160mV
INA219_GAIN_320MV = 0b11  # PGA gain ±320mV (default)

###########################
# Bus resolution constants#
###########################
INA219_BUS_RES_9BIT  = 0b0000  # 9-bit bus resolution
INA219_BUS_RES_10BIT = 0b0001  # 10-bit bus resolution
INA219_BUS_RES_11BIT = 0b0010  # 11-bit bus resolution
INA219_BUS_RES_12BIT = 0b0011  # 12-bit bus resolution (default)

###########################
# Shunt resolution consts #
###########################
INA219_SHUNT_RES_9BIT_1S    = 0b0000  # 9-bit, 1 sample
INA219_SHUNT_RES_10BIT_1S   = 0b0001  # 10-bit, 1 sample
INA219_SHUNT_RES_11BIT_1S   = 0b0010  # 11-bit, 1 sample
INA219_SHUNT_RES_12BIT_1S   = 0b0011  # 12-bit, 1 sample (default)
INA219_SHUNT_RES_12BIT_2S   = 0b1001  # 12-bit, 2 samples averaged
INA219_SHUNT_RES_12BIT_4S   = 0b1010  # 12-bit, 4 samples averaged
INA219_SHUNT_RES_12BIT_8S   = 0b1011  # 12-bit, 8 samples averaged
INA219_SHUNT_RES_12BIT_16S  = 0b1100  # 12-bit, 16 samples averaged
INA219_SHUNT_RES_12BIT_32S  = 0b1101  # 12-bit, 32 samples averaged
INA219_SHUNT_RES_12BIT_64S  = 0b1110  # 12-bit, 64 samples averaged
INA219_SHUNT_RES_12BIT_128S = 0b1111  # 12-bit, 128 samples averaged

###########################
# Mode constants          #
###########################
INA219_MODE_POWER_DOWN      = 0b000  # Power-down
INA219_MODE_SHUNT_TRIG      = 0b001  # Shunt voltage, triggered
INA219_MODE_BUS_TRIG        = 0b010  # Bus voltage, triggered
INA219_MODE_SHUNT_BUS_TRIG  = 0b011  # Shunt and bus, triggered
INA219_MODE_ADC_OFF         = 0b100  # ADC off (disabled)
INA219_MODE_SHUNT_CONT      = 0b101  # Shunt voltage, continuous
INA219_MODE_BUS_CONT        = 0b110  # Bus voltage, continuous
INA219_MODE_SHUNT_BUS_CONT  = 0b111  # Shunt and bus, continuous (default)


class INA219:
    """
    MicroPython class for the INA219 Zero-Drift, Bi-directional
    Current/Power Monitor. Communicates over I2C.
    """

    def __init__(self, i2c=None, address=INA219_ADDRESS):
        """
        Initialize the INA219.

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
                raise Exception("Board not recognized, please pass an I2C object manually")

        self.address = address

        # Internal calibration values
        self._current_lsb = 0.0
        self._power_lsb   = 0.0
        self._v_shunt_max = 0.0
        self._v_bus_max   = 0.0
        self._r_shunt     = 0.0

    # -------------------------------------------------------------------------
    # Initialization and configuration
    # -------------------------------------------------------------------------

    def begin(self):
        """
        Verify communication with the INA219.

        :return: True if device is reachable, False otherwise
        """
        try:
            self.i2c.readfrom(self.address, 1)
            return True
        except:
            return False

    def configure(self,
                  range=INA219_RANGE_32V,
                  gain=INA219_GAIN_320MV,
                  bus_res=INA219_BUS_RES_12BIT,
                  shunt_res=INA219_SHUNT_RES_12BIT_1S,
                  mode=INA219_MODE_SHUNT_BUS_CONT):
        """
        Configure the INA219 measurement range, gain, resolution, and mode.

        :param range:     INA219_RANGE_16V or INA219_RANGE_32V (default)
        :param gain:      INA219_GAIN_40MV / 80MV / 160MV / 320MV (default)
        :param bus_res:   INA219_BUS_RES_9BIT to 12BIT (default 12BIT)
        :param shunt_res: INA219_SHUNT_RES_* constant (default 12BIT_1S)
        :param mode:      INA219_MODE_* constant (default SHUNT_BUS_CONT)
        :return: True on success
        """
        config = (range << 13) | (gain << 11) | (bus_res << 7) | (shunt_res << 3) | mode

        if range == INA219_RANGE_32V:
            self._v_bus_max = 32.0
        elif range == INA219_RANGE_16V:
            self._v_bus_max = 16.0

        if gain == INA219_GAIN_320MV:
            self._v_shunt_max = 0.32
        elif gain == INA219_GAIN_160MV:
            self._v_shunt_max = 0.16
        elif gain == INA219_GAIN_80MV:
            self._v_shunt_max = 0.08
        elif gain == INA219_GAIN_40MV:
            self._v_shunt_max = 0.04

        self._writeRegister16(INA219_REG_CONFIG, config)
        return True

    def calibrate(self, r_shunt=0.1, i_max_expected=2.0):
        """
        Calibrate the INA219 for a specific shunt resistor and expected max current.

        :param r_shunt:        Shunt resistor value in Ohms (default 0.1)
        :param i_max_expected: Maximum expected current in Amps (default 2.0)
        :return: True on success
        """
        self._r_shunt = r_shunt

        minimum_lsb = i_max_expected / 32767.0

        # Round up to nearest 0.0001 A step
        self._current_lsb = math.ceil(minimum_lsb / 0.0001) * 0.0001

        self._power_lsb = self._current_lsb * 20.0

        calibration_value = int(0.04096 / (self._current_lsb * r_shunt))

        self._writeRegister16(INA219_REG_CALIBRATION, calibration_value)
        return True

    # -------------------------------------------------------------------------
    # Measurements
    # -------------------------------------------------------------------------

    def readBusPower(self):
        """
        Read the calculated bus power.

        :return: Power in Watts
        """
        return self._readRegister16(INA219_REG_POWER) * self._power_lsb

    def readShuntCurrent(self):
        """
        Read the calculated shunt current.

        :return: Current in Amps
        """
        return self._readRegister16(INA219_REG_CURRENT) * self._current_lsb

    def readShuntVoltage(self):
        """
        Read the shunt voltage.

        :return: Voltage in Volts (raw register value / 100000)
        """
        return self._readRegister16(INA219_REG_SHUNTVOLTAGE) / 100000.0

    def readBusVoltage(self):
        """
        Read the bus voltage. The raw register value is right-shifted by 3
        (lowest 3 bits are status flags) and scaled by 4 mV/LSB.

        :return: Voltage in Volts
        """
        raw = self._readRegister16(INA219_REG_BUSVOLTAGE)
        # Treat as unsigned for bus voltage register
        if raw < 0:
            raw += 65536
        raw >>= 3
        return raw * 0.004

    # -------------------------------------------------------------------------
    # Configuration readback
    # -------------------------------------------------------------------------

    def getRange(self):
        """
        Read the voltage range setting from the config register.

        :return: INA219_RANGE_16V or INA219_RANGE_32V
        """
        value = self._readRegister16(INA219_REG_CONFIG)
        return (value & 0b0010000000000000) >> 13

    def getGain(self):
        """
        Read the PGA gain setting from the config register.

        :return: INA219_GAIN_* constant
        """
        value = self._readRegister16(INA219_REG_CONFIG)
        return (value & 0b0001100000000000) >> 11

    def getBusRes(self):
        """
        Read the bus ADC resolution setting from the config register.

        :return: INA219_BUS_RES_* constant
        """
        value = self._readRegister16(INA219_REG_CONFIG)
        return (value & 0b0000011110000000) >> 7

    def getShuntRes(self):
        """
        Read the shunt ADC resolution setting from the config register.

        :return: INA219_SHUNT_RES_* constant
        """
        value = self._readRegister16(INA219_REG_CONFIG)
        return (value & 0b0000000001111000) >> 3

    def getMode(self):
        """
        Read the operating mode from the config register.

        :return: INA219_MODE_* constant
        """
        value = self._readRegister16(INA219_REG_CONFIG)
        return value & 0b0000000000000111

    # -------------------------------------------------------------------------
    # Limit helpers
    # -------------------------------------------------------------------------

    def getMaxPossibleCurrent(self):
        """
        Calculate the maximum possible current based on shunt voltage and resistor.

        :return: Maximum possible current in Amps
        """
        return self._v_shunt_max / self._r_shunt

    def getMaxCurrent(self):
        """
        Calculate the maximum current the calibration supports.

        :return: Maximum current in Amps
        """
        max_current  = self._current_lsb * 32767
        max_possible = self.getMaxPossibleCurrent()
        return min(max_current, max_possible)

    def getMaxShuntVoltage(self):
        """
        Calculate the maximum shunt voltage based on calibration.

        :return: Maximum shunt voltage in Volts
        """
        max_voltage = self.getMaxCurrent() * self._r_shunt
        return min(max_voltage, self._v_shunt_max)

    def getMaxPower(self):
        """
        Calculate the maximum power based on calibration and bus voltage range.

        :return: Maximum power in Watts
        """
        return self.getMaxCurrent() * self._v_bus_max

    # -------------------------------------------------------------------------
    # Private: I2C register access
    # -------------------------------------------------------------------------

    def _readRegister16(self, reg):
        """
        Read a 16-bit signed value from a register.

        :param reg: Register address
        :return: Signed 16-bit integer
        """
        try:
            self.i2c.writeto(self.address, bytes([reg]))
            time.sleep_ms(1)
            data = self.i2c.readfrom(self.address, 2)
            raw = (data[0] << 8) | data[1]
            # Convert to signed 16-bit
            return raw if raw < 0x8000 else raw - 0x10000
        except:
            return 0

    def _writeRegister16(self, reg, val):
        """
        Write a 16-bit value to a register (MSB first).

        :param reg: Register address
        :param val: 16-bit value to write
        """
        try:
            msb = (val >> 8) & 0xFF
            lsb = val & 0xFF
            self.i2c.writeto(self.address, bytes([reg, msb, lsb]))
        except:
            pass