# FILE: bmp280.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython library for the BMP280 temperature and pressure sensor
# LAST UPDATED: 2025-01-15

import time
from machine import I2C, Pin
from os import uname
from bmp280_constants import *


class BMP280:
    """
    MicroPython class for the Bosch BMP280 temperature and pressure sensor.
    Supports temperature, pressure, and altitude measurements.
    """

    def __init__(self, i2c=None, address=BMP280_I2C_ALT_ADDR):
        """
        Initialize the BMP280 sensor.

        :param i2c: Initialized I2C object
        :param address: I2C address of the sensor
        """
        if i2c != None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.address = address
        self.seaLevelPressure = 1013.23
        self.tFine = 0.0
        self.ctrlMeas = 0x00
        self.config = 0x00

        if not self.begin():
            raise Exception(
                "BMP280 initialization failed! Check wiring and I2C address."
            )

    def _read8(self, register):
        """Read a single byte from a register."""
        self.i2c.writeto(self.address, bytes([register]))
        return self.i2c.readfrom(self.address, 1)[0]

    def _readBytes(self, register, length):
        """Read multiple bytes from a register."""
        self.i2c.writeto(self.address, bytes([register]))
        return self.i2c.readfrom(self.address, length)

    def _write8(self, register, value):
        """Write a single byte to a register."""
        value = value & 0xFF
        self.i2c.writeto(self.address, bytes([register, value]))
        time.sleep_us(100)

    def begin(
        self,
        mode=SLEEP_MODE,
        presOversampling=OVERSAMPLING_X16,
        tempOversampling=OVERSAMPLING_X2,
        iirFilter=IIR_FILTER_OFF,
        standby=STANDBY_0_5MS,
    ):
        """Initialize the BMP280 with specified settings."""
        self.reset()
        time.sleep_ms(10)

        chipId = self._read8(BMP280_CHIP_ID)
        if chipId != BMP280_ID:
            return False

        self._loadCalibrationParams()
        self.setIIRFilter(iirFilter)
        self.setStandbyTime(standby)
        self.setOversampling(presOversampling, tempOversampling)
        self.setMode(mode)

        return True

    def reset(self):
        """Soft reset the BMP280 sensor."""
        self._write8(BMP280_RESET, RESET_CODE)

    def _loadCalibrationParams(self):
        """Read calibration parameters from the sensor."""
        calib = self._readBytes(BMP280_CALIB, 24)

        self.digT1 = calib[1] << 8 | calib[0]
        self.digT2 = self._toSigned(calib[3] << 8 | calib[2], 16)
        self.digT3 = self._toSigned(calib[5] << 8 | calib[4], 16)

        self.digP1 = calib[7] << 8 | calib[6]
        self.digP2 = self._toSigned(calib[9] << 8 | calib[8], 16)
        self.digP3 = self._toSigned(calib[11] << 8 | calib[10], 16)
        self.digP4 = self._toSigned(calib[13] << 8 | calib[12], 16)
        self.digP5 = self._toSigned(calib[15] << 8 | calib[14], 16)
        self.digP6 = self._toSigned(calib[17] << 8 | calib[16], 16)
        self.digP7 = self._toSigned(calib[19] << 8 | calib[18], 16)
        self.digP8 = self._toSigned(calib[21] << 8 | calib[20], 16)
        self.digP9 = self._toSigned(calib[23] << 8 | calib[22], 16)

    def _toSigned(self, value, bits):
        """Convert unsigned value to signed."""
        if value & (1 << (bits - 1)):
            value -= 1 << bits
        return value

    def setMode(self, mode):
        """Set sensor operating mode."""
        self.ctrlMeas = (self.ctrlMeas & 0xFC) | (mode & 0x03)
        self._write8(BMP280_CTRL_MEAS, self.ctrlMeas)

    def setOversampling(self, presOversampling, tempOversampling):
        """Set oversampling for pressure and temperature."""
        self.ctrlMeas = (
            ((tempOversampling & 0x07) << 5)
            | ((presOversampling & 0x07) << 2)
            | (self.ctrlMeas & 0x03)
        )
        self._write8(BMP280_CTRL_MEAS, self.ctrlMeas)

    def setIIRFilter(self, iirFilter):
        """Set IIR filter setting."""
        self.config = (self.config & 0xE3) | ((iirFilter & 0x07) << 2)
        self._write8(BMP280_CONFIG, self.config)

    def setStandbyTime(self, standby):
        """Set standby time between measurements in normal mode."""
        self.config = (self.config & 0x1F) | ((standby & 0x07) << 5)
        self._write8(BMP280_CONFIG, self.config)

    def setSeaLevelPressure(self, pressure):
        """Set sea level pressure for altitude calculation."""
        self.seaLevelPressure = pressure

    def _readRawTemp(self):
        data = self._readBytes(BMP280_TEMP_MSB, 3)
        return (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)

    def _readRawPress(self):
        data = self._readBytes(BMP280_PRESS_MSB, 3)
        return (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)

    def _compensateTemp(self, adcTemp):
        var1 = (adcTemp / 16384.0 - self.digT1 / 1024.0) * self.digT2
        var2 = ((adcTemp / 131072.0 - self.digT1 / 8192.0) ** 2) * self.digT3
        self.tFine = var1 + var2
        return self.tFine / 5120.0

    def _compensatePress(self, adcPress):
        var1 = self.tFine / 2.0 - 64000.0
        var2 = var1 * var1 * self.digP6 / 32768.0
        var2 = var2 + var1 * self.digP5 * 2.0
        var2 = var2 / 4.0 + self.digP4 * 65536.0
        var1 = (self.digP3 * var1 * var1 / 524288.0 + self.digP2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.digP1
        if var1 == 0:
            return 0
        pressure = 1048576.0 - adcPress
        pressure = (pressure - var2 / 4096.0) * 6250.0 / var1
        var1 = self.digP9 * pressure * pressure / 2147483648.0
        var2 = pressure * self.digP8 / 32768.0
        pressure = pressure + (var1 + var2 + self.digP7) / 16.0
        return pressure

    def getTemperature(self):
        """Get temperature in Celsius."""
        adcTemp = self._readRawTemp()
        return self._compensateTemp(adcTemp)

    def getPressure(self):
        """Get pressure in hPa."""
        adcTemp = self._readRawTemp()
        self._compensateTemp(adcTemp)
        adcPress = self._readRawPress()
        pressure = self._compensatePress(adcPress)
        return pressure / 100.0

    def getMeasurements(self):
        """Get temperature, pressure, and altitude measurements."""
        temperature = self.getTemperature()
        pressure = self.getPressure()
        altitude = (
            (pow(self.seaLevelPressure / pressure, 0.190223) - 1.0)
            * (temperature + 273.15)
            / 0.0065
        )
        return (temperature, pressure, altitude)

    def getAltitude(self):
        """Get altitude in meters."""
        return self.getMeasurements()[2]

    def readAllValues(self):
        """Read temperature, pressure, and altitude."""
        return self.getMeasurements()
