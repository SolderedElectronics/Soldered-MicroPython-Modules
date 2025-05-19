import struct
import time

class BME280:
    def __init__(self, i2c, address=0x76):
        self.i2c = i2c
        self.address = address
        self._load_calibration_params()
        self._configure_sensor()

    def _read8(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    def _read16(self, register):
        data = self.i2c.readfrom_mem(self.address, register, 2)
        return data[1] << 8 | data[0]

    def _read16le(self, register):
        data = self.i2c.readfrom_mem(self.address, register, 2)
        return data[0] | (data[1] << 8)

    def _read_signed16le(self, register):
        result = self._read16le(register)
        if result > 32767:
            result -= 65536
        return result

    def _load_calibration_params(self):
        # Temperature calibration
        self.dig_T1 = self._read16le(0x88)
        self.dig_T2 = self._read_signed16le(0x8A)
        self.dig_T3 = self._read_signed16le(0x8C)

        # Pressure calibration
        self.dig_P1 = self._read16le(0x8E)
        self.dig_P2 = self._read_signed16le(0x90)
        self.dig_P3 = self._read_signed16le(0x92)
        self.dig_P4 = self._read_signed16le(0x94)
        self.dig_P5 = self._read_signed16le(0x96)
        self.dig_P6 = self._read_signed16le(0x98)
        self.dig_P7 = self._read_signed16le(0x9A)
        self.dig_P8 = self._read_signed16le(0x9C)
        self.dig_P9 = self._read_signed16le(0x9E)

        # Humidity calibration
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

    def _configure_sensor(self):
        self.i2c.writeto_mem(self.address, 0xF2, b'\x01')  # Humidity oversampling x1
        self.i2c.writeto_mem(self.address, 0xF4, b'\x27')  # Temp/Pressure oversampling x1, Normal mode
        self.i2c.writeto_mem(self.address, 0xF5, b'\xA0')  # Standby 1000ms, Filter off

    def read_raw_data(self):
        # Burst read of 8 bytes from 0xF7
        data = self.i2c.readfrom_mem(self.address, 0xF7, 8)
        raw_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        raw_temp = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        raw_hum = (data[6] << 8) | data[7]
        return raw_temp, raw_press, raw_hum

    def read_temperature(self, adc_T):
        var1 = (((adc_T >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((adc_T >> 4) - self.dig_T1) * ((adc_T >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        self.t_fine = var1 + var2
        return ((self.t_fine * 5 + 128) >> 8)/100

    def read_pressure(self, adc_P):
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
        return (((p + var1 + var2) >> 8) + (self.dig_P7 << 4))/25600

    def read_humidity(self, adc_H):
        v_x1 = self.t_fine - 76800
        v_x1 = (((((adc_H << 14) - (self.dig_H4 << 20) - (self.dig_H5 * v_x1)) + 16384) >> 15) *
                (((((((v_x1 * self.dig_H6) >> 10) * (((v_x1 * self.dig_H3) >> 11) + 32768)) >> 10) + 2097152) *
                  self.dig_H2 + 8192) >> 14))
        v_x1 = v_x1 - (((((v_x1 >> 15) * (v_x1 >> 15)) >> 7) * self.dig_H1) >> 4)
        v_x1 = max(min(v_x1, 419430400), 0)
        return (v_x1 >> 12)/1024

    def read_all_values(self):
        raw_temp, raw_press, raw_hum = self.read_raw_data()
        temperature = self.read_temperature(raw_temp)
        pressure = self.read_pressure(raw_press)
        humidity = self.read_humidity(raw_hum)
        return temperature, pressure, humidity

    def calculate_altitude(self):
        seaLevel = 1013.25
        data = self.i2c.readfrom_mem(self.address, 0xF7, 8)
        raw_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)

        return 44330.0 * (1.0 - pow(self.read_pressure(raw_press) / seaLevel, 0.1903))

