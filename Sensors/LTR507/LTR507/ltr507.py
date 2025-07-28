# FILE: LTR507.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: A Micropython module for the LTR-507 Light and proximity sensor
# LAST UPDATED: 2025-06-10

from machine import I2C, Pin
from os import uname
from time import sleep_ms
from ltr507_config import *


class LTR507:
    def __init__(self, i2c=None, address=0x3A):
        """
        Initialize the LTR507 sensor.

        :param i2c: Initialized I2C object
        :param address: I2C address of the sensor (default 0x3A)
        """
        if i2c != None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")
        self.address = address
        self.raw = bytearray(2)  # Buffer for reading multi-byte registers

    def _read_register(self, reg, length=1):
        """
        Read bytes from a sensor register.

        :param reg: Register address to read from
        :param length: Number of bytes to read (default 1)
        :return: Bytes read from the register
        """
        return self.i2c.readfrom_mem(self.address, reg, length)

    def _write_register(self, reg, data):
        """
        Write a single byte to a sensor register.

        :param reg: Register address to write to
        :param data: Byte value to write
        """
        self.i2c.writeto_mem(self.address, reg, bytes([data]))

    def _write_registers(self, reg, values):
        """
        Write multiple bytes to consecutive sensor registers.

        :param reg: Starting register address
        :param values: Iterable of byte values to write
        """
        self.i2c.writeto_mem(self.address, reg, bytes(values))

    def begin(self):
        """
        Initialize the sensor with default configuration settings.
        Enables ALS and PS modes and sets recommended measurement parameters.
        """
        self.set_als_mode(True)
        self.set_ps_mode(True)
        self.set_als_gain(LTR507_ALS_GAIN_RANGE1)
        self.set_als_bitwidth(LTR507_ALS_ADC_BIT_WIDTH_16BIT)
        self.set_als_meas_rate(LTR507_ALS_MEASUREMENT_RATE_100MS)
        self.set_led_pulse_freq(LTR507_LED_PULSE_FREQ_60KHZ)
        self.set_led_duty_cycle(LTR507_LED_CURRENT_DUTY_DEFAULT)
        self.set_ps_meas_rate(LTR507_PS_MEASUREMENT_RATE_100MS)
        self.set_led_peak_current(LTR507_LED_PEAK_CURRENT_50MA)
        self.set_ps_num_pulses(1)

    def set_ps_mode(self, mode):
        """
        Enable or disable proximity sensing mode.

        :param mode: Boolean indicating whether to enable (True) or disable (False) PS mode
        """
        val = self._read_register(LTR507_PS_CONTR_REG)[0]
        val &= ~LTR507_PS_MODE_MASK
        val |= (mode << LTR507_PS_MODE_SHIFT) & LTR507_PS_MODE_MASK
        self._write_register(LTR507_PS_CONTR_REG, val)

    def set_als_mode(self, mode):
        """
        Enable or disable ambient light sensing mode.

        :param mode: Boolean indicating whether to enable (True) or disable (False) ALS mode
        """
        val = self._read_register(LTR507_ALS_CONTR_REG)[0]
        if mode:
            val |= 0x02  # Set bit 1
        else:
            val &= 0xFD  # Clear bit 1
        self._write_register(LTR507_ALS_CONTR_REG, val)

    def set_led_pulse_freq(self, freq):
        """
        Set the LED pulse frequency for proximity sensing.

        :param freq: Frequency constant (e.g., LTR507_LED_PULSE_FREQ_60KHZ)
        """
        val = self._read_register(LTR507_PS_LED_REG)[0]
        val &= ~LTR507_LED_PULSE_FREQ_MASK
        val |= (freq << LTR507_LED_PULSE_FREQ_SHIFT) & LTR507_LED_PULSE_FREQ_MASK
        self._write_register(LTR507_PS_LED_REG, val)

    def set_led_duty_cycle(self, duty):
        """
        Set the duty cycle of the proximity LED.

        :param duty: Duty cycle constant (e.g., LTR507_LED_CURRENT_DUTY_DEFAULT)
        """
        val = self._read_register(LTR507_PS_LED_REG)[0]
        val &= ~LTR507_LED_DUTY_CYCLE_MASK
        val |= (duty << LTR507_LED_DUTY_CYCLE_SHIFT) & LTR507_LED_DUTY_CYCLE_MASK
        self._write_register(LTR507_PS_LED_REG, val)

    def set_ps_meas_rate(self, rate):
        """
        Set the measurement rate for proximity sensing.

        :param rate: Measurement rate constant (e.g., LTR507_PS_MEASUREMENT_RATE_100MS)
        """
        val = rate & LTR507_PS_MEAS_RATE_MASK
        self._write_register(LTR507_PS_MEAS_RATE_REG, val)

    def set_led_peak_current(self, current):
        """
        Set the peak drive current of the proximity LED.

        :param current: Current constant (e.g., LTR507_LED_PEAK_CURRENT_50MA)
        """
        val = self._read_register(LTR507_PS_LED_REG)[0]
        val &= ~LTR507_LED_PEAK_CURRENT_MASK
        val |= current & LTR507_LED_PEAK_CURRENT_MASK
        self._write_register(LTR507_PS_LED_REG, val)

    def set_ps_num_pulses(self, num_pulses):
        """
        Set the number of LED pulses for each proximity measurement.

        :param num_pulses: Integer value between 1 and 15
        """
        num_pulses = max(1, min(15, num_pulses))
        val = num_pulses & LTR507_PS_PULSES_MASK
        self._write_register(LTR507_PS_N_PULSES_REG, val)

    def set_als_gain(self, gain):
        """
        Set the analog gain for ambient light sensing.

        :param gain: Gain constant (e.g., LTR507_ALS_GAIN_RANGE1)
        """
        val = self._read_register(LTR507_ALS_CONTR_REG)[0]
        val &= ~LTR507_ALS_GAIN_MASK
        val |= (gain << LTR507_ALS_GAIN_SHIFT) & LTR507_ALS_GAIN_MASK
        self._write_register(LTR507_ALS_CONTR_REG, val)

    def set_als_bitwidth(self, bitwidth):
        """
        Set the ADC resolution (bit width) for ambient light measurements.

        :param bitwidth: Bit width constant (e.g., LTR507_ALS_ADC_BIT_WIDTH_16BIT)
        """
        val = self._read_register(LTR507_ALS_MEAS_PATE_REG)[0]
        val &= ~LTR507_ALS_ADC_BIT_WIDTH_MASK
        val |= (
            bitwidth << LTR507_ALS_ADC_BIT_WIDTH_SHIFT
        ) & LTR507_ALS_ADC_BIT_WIDTH_MASK
        self._write_register(LTR507_ALS_MEAS_PATE_REG, val)

    def set_als_meas_rate(self, rate):
        """
        Set the ambient light sensor measurement rate.

        :param rate: Measurement rate constant (e.g., LTR507_ALS_MEASUREMENT_RATE_100MS)
        """
        val = self._read_register(LTR507_ALS_MEAS_PATE_REG)[0]
        val &= ~LTR507_ALS_MEASURE_RATE_MASK
        val |= (rate << LTR507_ALS_MEASURE_RATE_SHIFT) & LTR507_ALS_MEASURE_RATE_MASK
        self._write_register(LTR507_ALS_MEAS_PATE_REG, val)

    def getLightIntensity(self):
        """
        Read and return the current ambient light level.

        :return: 16-bit integer light value (0 if data not ready)
        """
        status = self._read_register(LTR507_ALS_PS_STATUS_REG)[0]
        if not (status & 0x04):  # Check if ALS data is valid
            return 0
        data = self._read_register(LTR507_ALS_DATA_0_REG, 2)
        return data[0] | (data[1] << 8)  # Combine low and high bytes

    def getProximity(self):
        """
        Read and return the current proximity sensor value.

        :return: 16-bit integer proximity value
        """
        data = self._read_register(LTR507_PS_DATA_LOW_REG, 2)
        low = data[0] & LTR507_PS_DATA_LOW_MASK
        high = data[1] & LTR507_PS_DATA_HIGH_MASK
        return low | (high << 8)  # Combine low and high bytes
