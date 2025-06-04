# FILE: bmp180.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython library for the BMP180 temperature and pressure sensor
# LAST UPDATED: 2025-06-04

from machine import I2C, Pin
from os import uname
import time
import struct

# BMP180 default I2C address
BMP180_I2C_ADDR = 0x77

# Registers
REG_CALIB = 0xAA
REG_CONTROL = 0xF4
REG_DATA = 0xF6

CMD_READ_TEMP = 0x2E
CMD_READ_PRESSURE = 0x34

class BMP180:
    def __init__(self, i2c=None, address: int = BMP180_I2C_ADDR, oss: int = 0):
        """
        Initialize BMP180 sensor.

        :param i2c: Initialized I2C instance
        :param address: I2C address of the sensor
        :param oss: Oversampling setting (0–3), default 0
        """
        if i2c != None:
            self.i2c = i2c
        else:
            if uname().sysname == "esp32" or uname().sysname == "esp8266":
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.address = address
        self.oss = oss
        self.cal = {}
        self._read_calibration_data()

    def _read_calibration_data(self):
        """
        Reads calibration coefficients from the BMP180's EEPROM.
        """
        raw = self.i2c.readfrom_mem(self.address, REG_CALIB, 22)
        vals = struct.unpack('>hhhHHHhhhhh', raw)

        self.cal['AC1'] = vals[0]
        self.cal['AC2'] = vals[1]
        self.cal['AC3'] = vals[2]
        self.cal['AC4'] = vals[3]
        self.cal['AC5'] = vals[4]
        self.cal['AC6'] = vals[5]
        self.cal['B1'] = vals[6]
        self.cal['B2'] = vals[7]
        self.cal['MB'] = vals[8]
        self.cal['MC'] = vals[9]
        self.cal['MD'] = vals[10]

    def _read_raw_temp(self):
        """
        Starts temperature measurement and returns raw temperature.
        """
        self.i2c.writeto_mem(self.address, REG_CONTROL, bytes([CMD_READ_TEMP]))
        time.sleep_ms(5)
        raw = self.i2c.readfrom_mem(self.address, REG_DATA, 2)
        return struct.unpack('>H', raw)[0]

    def _read_raw_pressure(self):
        """
        Starts pressure measurement and returns raw pressure.
        """
        self.i2c.writeto_mem(self.address, REG_CONTROL, bytes([CMD_READ_PRESSURE + (self.oss << 6)]))
        time.sleep_ms(2 + (3 << self.oss))
        raw = self.i2c.readfrom_mem(self.address, REG_DATA, 3)
        msb, lsb, xlsb = struct.unpack('BBB', raw)
        return ((msb << 16) + (lsb << 8) + xlsb) >> (8 - self.oss)

    def read_temperature(self) -> float:
        """
        Reads and returns the true temperature in Celsius.
        """
        UT = self._read_raw_temp()
        X1 = ((UT - self.cal['AC6']) * self.cal['AC5']) >> 15
        X2 = (self.cal['MC'] << 11) // (X1 + self.cal['MD'])
        self._B5 = X1 + X2
        T = (self._B5 + 8) >> 4
        return T / 10.0

    def read_pressure(self) -> int:
        """
        Reads and returns the true pressure in HectoPascals.
        """
        self.read_temperature()  # must be called first to compute _B5
        UP = self._read_raw_pressure()

        B6 = self._B5 - 4000
        X1 = (self.cal['B2'] * (B6 * B6 >> 12)) >> 11
        X2 = (self.cal['AC2'] * B6) >> 11
        X3 = X1 + X2
        B3 = (((self.cal['AC1'] * 4 + X3) << self.oss) + 2) >> 2

        X1 = (self.cal['AC3'] * B6) >> 13
        X2 = (self.cal['B1'] * (B6 * B6 >> 12)) >> 16
        X3 = ((X1 + X2) + 2) >> 2
        B4 = (self.cal['AC4'] * (X3 + 32768)) >> 15
        B7 = (UP - B3) * (50000 >> self.oss)

        if B7 < 0x80000000:
            P = (B7 * 2) // B4
        else:
            P = (B7 // B4) * 2

        X1 = (P >> 8) * (P >> 8)
        X1 = (X1 * 3038) >> 16
        X2 = (-7357 * P) >> 16
        P = P + ((X1 + X2 + 3791) >> 4)
        return P/100