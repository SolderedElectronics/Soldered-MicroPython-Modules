# FILE: bme280.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython library for the BME280 temperature, pressure, and humidity sensor
# LAST UPDATED: 2025-05-23

import struct
import time
from machine import I2C, Pin
from os import uname


class BME280:
    """
    MicroPython class for the Bosch BME280 environmental sensor.
    Supports temperature, pressure, humidity, and altitude calculations.
    """

    # Constructor
    def __init__(self, i2c=None, address=0x76):
        """
        Initialize the BME280 sensor.

        :param i2c: Initialized I2C object
        :param address: I2C address of the sensor (default 0x76)
        """
        if i2c != None:
            self.i2c = i2c
        else:
            if uname().sysname == "esp32" or uname().sysname == "esp8266":
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")
                
        self.address = address
        self._load_calibration_params()
        self._configure_sensor()

    # Read 8-bit unsigned value from a register
    def _read8(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    # Read 16-bit unsigned value (MSB first) from a register
    def _read16(self, register):
        data = self.i2c.readfrom_mem(self.address, register, 2)
        return data[1] << 8 | data[0]

    # Read 16-bit unsigned value (LSB first)
    def _read16le(self, register):
        data = self.i2c.readfrom_mem(self.address, register, 2)
        return data[0] | (data[1] << 8)

    # Read 16-bit signed value (LSB first)
    def _read_signed16le(self, register):
        result = self._read16le(register)
        if result > 32767:
            result -= 65536
        return result

    # Load all factory calibration parameters from sensor registers
    def _load_calibration_params(self):
        """
        Read and store all sensor calibration parameters from internal registers.
        Required for temperature, pressure, and humidity compensation.
        """
        self.dig_T1 = self._read16le(0x88)
        self.dig_T2 = self._read_signed16le(0x8A)
        self.dig_T3 = self._read_signed16le(0x8C)

        self.dig_P1 = self._read16le(0x8E)
        self.dig_P2 = self._read_signed16le(0x90)
        self.dig_P3 = self._read_signed16le(0x92)
        self.dig_P4 = self._read_signed16le(0x94)
        self.dig_P5 = self._read_signed16le(0x96)
        self.dig_P6 = self._read_signed16le(0x98)
        self.dig_P7 = self._read_signed16le(0x9A)
        self.dig_P8 = self._read_signed16le(0x9C)
        self.dig_P9 = self._read_signed16le(0x9E)

        self.dig_H1 = self._read8(0xA1)
        self.dig_H2 = self._read_signed16le(0xE1)
        self.dig_H3 = self._read8(0xE3)
        e4 = self._read8(0xE4)
        e5 = self._read8(0xE5)
        e6 = self._read8(0xE6)
        e7 = self._read8(0xE7)
        self.dig_H4 = (e4 << 4) | (e5 & 0x0F)
        self.dig_H5 = (e6 << 4) | (e5 >> 4)
        self.dig_H6 = e7 if e7 < 128 else e7 - 256

    # Configure sensor settings (oversampling and mode)
    def _configure_sensor(self):
        """
        Write configuration registers to enable humidity, pressure,
        and temperature measurements with oversampling = x1, normal mode.
        """
        self.i2c.writeto_mem(self.address, 0xF2, b"\x01")  # Humidity oversampling x1
        self.i2c.writeto_mem(
            self.address, 0xF4, b"\x27"
        )  # Temp/Pressure oversampling x1, Normal mode
        self.i2c.writeto_mem(self.address, 0xF5, b"\xa0")  # Standby 1000ms, Filter off

    # Read raw sensor data for temperature, pressure, and humidity
    def read_raw_data(self):
        """
        Read raw temperature, pressure, and humidity data from the sensor.

        :return: (raw_temp, raw_press, raw_hum)
        """
        data = self.i2c.readfrom_mem(self.address, 0xF7, 8)
        raw_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_temp = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        raw_hum = (data[6] << 8) | data[7]
        return raw_temp, raw_press, raw_hum

    # Convert raw temperature to degrees Celsius
    def readTemperature(self, adc_T):
        """
        Convert raw temperature reading to degrees Celsius.

        :param adc_T: Raw temperature from read_raw_data
        :return: Temperature in °C
        """
        var1 = (((adc_T >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (
            ((((adc_T >> 4) - self.dig_T1) * ((adc_T >> 4) - self.dig_T1)) >> 12)
            * self.dig_T3
        ) >> 14
        self.t_fine = var1 + var2
        return ((self.t_fine * 5 + 128) >> 8) / 100

    # Convert raw pressure to hPa
    def readPressure(self, adc_P):
        """
        Convert raw pressure reading to hectoPascals (hPa).

        :param adc_P: Raw pressure from read_raw_data
        :return: Pressure in hPa
        """
        var1 = self.t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            return 0  # avoid division by zero
        p = 1048576 - adc_P
        p = ((p << 31) - var2) * 3125 // var1
        var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self.dig_P8 * p) >> 19
        return (((p + var1 + var2) >> 8) + (self.dig_P7 << 4)) / 25600

    # Convert raw humidity to relative humidity (%)
    def readHumidity(self, adc_H):
        """
        Convert raw humidity reading to percentage relative humidity.

        :param adc_H: Raw humidity from read_raw_data
        :return: Humidity in %RH
        """
        v_x1 = self.t_fine - 76800
        v_x1 = (
            (((adc_H << 14) - (self.dig_H4 << 20) - (self.dig_H5 * v_x1)) + 16384) >> 15
        ) * (
            (
                (
                    (
                        (
                            ((v_x1 * self.dig_H6) >> 10)
                            * (((v_x1 * self.dig_H3) >> 11) + 32768)
                        )
                        >> 10
                    )
                    + 2097152
                )
                * self.dig_H2
                + 8192
            )
            >> 14
        )
        v_x1 = v_x1 - (((((v_x1 >> 15) * (v_x1 >> 15)) >> 7) * self.dig_H1) >> 4)
        v_x1 = max(min(v_x1, 419430400), 0)
        return (v_x1 >> 12) / 1024

    # Read temperature, pressure, and humidity in one call
    def readAllValues(self):
        """
        Read and return compensated temperature, pressure, and humidity values.

        :return: (temperature °C, pressure hPa, humidity %)
        """
        raw_temp, raw_press, raw_hum = self.read_raw_data()
        temperature = self.readTemperature(raw_temp)
        pressure = self.readPressure(raw_press)
        humidity = self.readHumidity(raw_hum)
        return temperature, pressure, humidity

    # Calculate altitude from current pressure using sea-level reference
    def calculateAltitude(self):
        """
        Estimate altitude in meters from current pressure using standard sea-level pressure.

        :return: Altitude in meters
        """
        seaLevel = 1013.25  # hPa
        data = self.i2c.readfrom_mem(self.address, 0xF7, 8)
        raw_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        return 44330.0 * (1.0 - pow(self.readPressure(raw_press) / seaLevel, 0.1903))

