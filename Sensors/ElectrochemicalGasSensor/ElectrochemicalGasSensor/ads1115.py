# FILE: ads1115.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython driver for ADS1115 16-bit 4-channel ADC (helper for ElectrochemicalGasSensor)
# LAST UPDATED: 2026-05-21

import time

# Registers
_REG_CONVERT = 0x00
_REG_CONFIG = 0x01

# Config register bits
_OS_START_SINGLE = 0x8000
_OS_NOT_BUSY = 0x8000
_MODE_SINGLE = 0x0100

# PGA gain register values
_PGA_6_144V = 0x0000
_PGA_4_096V = 0x0200
_PGA_2_048V = 0x0400
_PGA_1_024V = 0x0600
_PGA_0_512V = 0x0800
_PGA_0_256V = 0x0A00

# Comparator disabled + default polarity (matches ADS1X15 reset() defaults)
_COMP_DEFAULTS = 0x000B

# User-facing gain index constants (passed to setGain)
ADS_GAIN_6_144V = 0
ADS_GAIN_4_096V = 1
ADS_GAIN_2_048V = 2
ADS_GAIN_1_024V = 4
ADS_GAIN_0_512V = 8
ADS_GAIN_0_256V = 16

_PGA_TABLE = {
    ADS_GAIN_6_144V: (_PGA_6_144V, 6.144),
    ADS_GAIN_4_096V: (_PGA_4_096V, 4.096),
    ADS_GAIN_2_048V: (_PGA_2_048V, 2.048),
    ADS_GAIN_1_024V: (_PGA_1_024V, 1.024),
    ADS_GAIN_0_512V: (_PGA_0_512V, 0.512),
    ADS_GAIN_0_256V: (_PGA_0_256V, 0.256),
}


class ADS1115:
    """16-bit 4-channel ADC over I2C. Used internally by ElectrochemicalGasSensor."""

    def __init__(self, i2c, address):
        self._i2c = i2c
        self._address = address
        self._gain_reg = _PGA_6_144V
        self._max_voltage = 6.144
        self._datarate = 4 << 5  # index 4 default

    def begin(self):
        """Return True if ADS1115 is found on I2C bus."""
        return self._address in self._i2c.scan()

    def setGain(self, gain):
        """Set PGA gain. Use ADS_GAIN_* constants."""
        self._gain_reg, self._max_voltage = _PGA_TABLE.get(gain, (_PGA_6_144V, 6.144))

    def setDataRate(self, rate):
        """Set data rate index 0-7. 0 = slowest, 7 = fastest."""
        if rate > 7:
            rate = 4
        self._datarate = rate << 5

    def readADC(self, pin):
        """Single-ended read on pin 0-3. Returns signed int16."""
        readmode = (4 + pin) << 12
        config = (
            _OS_START_SINGLE
            | readmode
            | self._gain_reg
            | _MODE_SINGLE
            | self._datarate
            | _COMP_DEFAULTS
        )
        self._writeRegister(_REG_CONFIG, config)
        while not self._conversionDone():
            time.sleep_ms(1)
        return self._getValue()

    def toVoltage(self, val):
        """Convert raw int16 to voltage in volts."""
        if val == 0:
            return 0.0
        return (self._max_voltage * val) / 32767.0

    def _conversionDone(self):
        return bool(self._readRegister(_REG_CONFIG) & _OS_NOT_BUSY)

    def _getValue(self):
        raw = self._readRegister(_REG_CONVERT)
        if raw & 0x8000:
            raw -= 0x10000
        return raw

    def _writeRegister(self, reg, value):
        self._i2c.writeto(
            self._address, bytes([reg, (value >> 8) & 0xFF, value & 0xFF])
        )

    def _readRegister(self, reg):
        self._i2c.writeto(self._address, bytes([reg]))
        data = self._i2c.readfrom(self._address, 2)
        return (data[0] << 8) | data[1]
