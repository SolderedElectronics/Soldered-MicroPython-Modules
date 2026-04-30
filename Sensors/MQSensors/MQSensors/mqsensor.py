# FILE: mqsensor.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: A MicroPython module for the MQ gas sensor family, supports native and Qwiic modes
# LAST UPDATED: 2026-04-30

import math
from os import uname
from machine import Pin, ADC
from Qwiic import Qwiic

REGRESSION_EXPONENTIAL = 1
REGRESSION_LINEAR = 0


class MQSensor(Qwiic):
    """
    Base class for MQ gas sensor family.
    Supports native (analog+digital GPIO pins) and Qwiic (I2C) modes.
    """

    def __init__(
        self,
        regression_method,
        Rs_R0_ratio,
        a,
        b,
        analog_pin=None,
        digital_pin=None,
        i2c=None,
        address=0x30,
        RL=10.0,
        R0=10.0,
    ):
        """
        Initialize the MQ gas sensor.

        Args:
            regression_method (int): REGRESSION_EXPONENTIAL or REGRESSION_LINEAR
            Rs_R0_ratio (float): Rs/R0 ratio in clean air for calibration
            a (float): regression coefficient a
            b (float): regression coefficient b
            analog_pin (int, optional): GPIO pin number for analog reading (native mode)
            digital_pin (int, optional): GPIO pin number for digital reading (native mode)
            i2c (I2C, optional): I2C object for Qwiic mode
            address (int): I2C address (default 0x30)
            RL (float): load resistance in kΩ (default 10)
            R0 (float): sensor baseline resistance in kΩ (set via calibrate())
        """
        self._regression_method = regression_method
        self._Rs_R0_ratio = Rs_R0_ratio
        self._a = a
        self._b = b
        self._RL = RL
        self._R0 = R0
        self._sensor_volt = 0.0
        self._digital_pin = None

        if analog_pin is not None:
            self.native = True
            sysname = uname().sysname
            if sysname in ("esp32", "Soldered Dasduino CONNECTPLUS"):
                self._voltage_res = 3.3
                self._adc_max = 4095
                self._analog_pin = ADC(Pin(analog_pin))
                self._analog_pin.atten(ADC.ATTN_11DB)
            elif sysname == "esp8266":
                self._voltage_res = 3.3
                self._adc_max = 1023
                self._analog_pin = ADC(Pin(analog_pin))
            else:
                self._voltage_res = 5.0
                self._adc_max = 1023
                self._analog_pin = ADC(Pin(analog_pin))
            if digital_pin is not None:
                self._digital_pin = Pin(digital_pin, Pin.IN)
        else:
            # Qwiic board uses 5V reference, 10-bit ADC
            self._voltage_res = 5.0
            self._adc_max = 1023
            super().__init__(i2c=i2c, address=address, native=False)

    def _read_voltage(self):
        if self.native:
            total = 0
            for _ in range(2):
                total += self._analog_pin.read()
            return (total / 2.0) * self._voltage_res / self._adc_max
        else:
            data = self.read_register(0, 2)
            if len(data) < 2:
                return 0.0
            adc = data[0] | (data[1] << 8)
            return adc / 1024.0 * self._voltage_res

    def update(self):
        """Read and store current sensor voltage. Call before readSensor() or calibrate()."""
        self._sensor_volt = self._read_voltage()

    def readSensor(self):
        """
        Calculate gas concentration in PPM based on last update() call.

        Returns:
            float: Gas concentration in PPM.
        """
        if self._sensor_volt <= 0 or self._R0 <= 0:
            return 0.0
        RS = (self._voltage_res * self._RL / self._sensor_volt) - self._RL
        if RS < 0:
            RS = 0.0
        ratio = RS / self._R0
        if ratio <= 0:
            return 0.0
        if self._regression_method == REGRESSION_EXPONENTIAL:
            ppm = self._a * math.pow(ratio, self._b)
        else:
            if self._a == 0:
                return 0.0
            ppm_log = (math.log10(ratio) - self._b) / self._a
            ppm = math.pow(10, ppm_log)
        return max(0.0, ppm)

    def calibrate(self, num_samples=10):
        """
        Calibrate the sensor in clean air. Sets R0 based on averaged readings.

        Args:
            num_samples (int): Number of readings to average (default 10).

        Returns:
            bool: True if calibration succeeded, False on error.
        """
        r0_sum = 0.0
        for _ in range(num_samples):
            self.update()
            if self._sensor_volt <= 0:
                return False
            RS_air = (self._voltage_res * self._RL / self._sensor_volt) - self._RL
            if RS_air < 0:
                RS_air = 0.0
            r0 = RS_air / self._Rs_R0_ratio
            if r0 < 0:
                r0 = 0.0
            r0_sum += r0
        r0_avg = r0_sum / num_samples
        if r0_avg == 0 or math.isinf(r0_avg):
            return False
        self._R0 = r0_avg
        return True

    def setR0(self, R0):
        """Set R0 directly (e.g. from a stored calibration value)."""
        self._R0 = R0

    def getR0(self):
        """Return current R0 value in kΩ."""
        return self._R0

    def setRL(self, RL):
        """Set load resistance in kΩ."""
        self._RL = RL

    def getRL(self):
        """Return current load resistance in kΩ."""
        return self._RL

    def setA(self, a):
        """Set regression coefficient a."""
        self._a = a

    def setB(self, b):
        """Set regression coefficient b."""
        self._b = b

    def setRegressionModel(self, method, a, b):
        """
        Override the regression model coefficients.

        Args:
            method (int): REGRESSION_EXPONENTIAL or REGRESSION_LINEAR
            a (float): coefficient a
            b (float): coefficient b
        """
        self._regression_method = method
        self._a = a
        self._b = b

    def digitalRead(self):
        """
        Read the digital output pin (native mode only).

        Returns:
            bool: True if gas threshold exceeded.

        Raises:
            Exception: If no digital pin was configured.
        """
        if self._digital_pin is not None:
            return bool(self._digital_pin.value())
        raise Exception("No digital pin configured")


class MQ2(MQSensor):
    """MQ-2: LPG, propane, hydrogen, smoke. Default coefficients for LPG."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_EXPONENTIAL, 9.83, 574.25, -2.222, analog_pin, digital_pin, i2c, address
        )


class MQ3(MQSensor):
    """MQ-3: alcohol, benzene, hexane. Default coefficients for alcohol."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_EXPONENTIAL, 60.0, 0.3934, -1.504, analog_pin, digital_pin, i2c, address
        )


class MQ4(MQSensor):
    """MQ-4: methane, natural gas. Default coefficients for CH4."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_EXPONENTIAL, 4.4, 1012.7, -2.786, analog_pin, digital_pin, i2c, address
        )


class MQ5(MQSensor):
    """MQ-5: natural gas, LPG. Default coefficients for LPG."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_EXPONENTIAL, 6.5, 80.897, -2.431, analog_pin, digital_pin, i2c, address
        )


class MQ6(MQSensor):
    """MQ-6: LPG, butane. Default coefficients for LPG."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_EXPONENTIAL, 10.0, 1009.2, -2.35, analog_pin, digital_pin, i2c, address
        )


class MQ7(MQSensor):
    """MQ-7: carbon monoxide. Default coefficients for CO."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_EXPONENTIAL, 27.5, 99.042, -1.518, analog_pin, digital_pin, i2c, address
        )


class MQ8(MQSensor):
    """MQ-8: hydrogen. Default coefficients for H2."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_EXPONENTIAL, 70.0, 976.97, -0.688, analog_pin, digital_pin, i2c, address
        )


class MQ9(MQSensor):
    """MQ-9: CO, flammable gases. Default coefficients for LPG."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_EXPONENTIAL, 9.6, 1000.5, -2.186, analog_pin, digital_pin, i2c, address
        )


class MQ131(MQSensor):
    """MQ-131: ozone. Default coefficients for O3."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_LINEAR, 1.0, 0.41195, -0.4708, analog_pin, digital_pin, i2c, address
        )


class MQ135(MQSensor):
    """MQ-135: NH3, NOx, benzene, CO2. Default coefficients for NH3."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_LINEAR, 1.0, -0.47712, 0.4491, analog_pin, digital_pin, i2c, address
        )


class MQ136(MQSensor):
    """MQ-136: hydrogen sulfide. No default coefficients - use setRegressionModel()."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_LINEAR, 1.0, 0.0, 0.0, analog_pin, digital_pin, i2c, address
        )


class MQ137(MQSensor):
    """MQ-137: ammonia. Default coefficients for NH3."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_LINEAR, 1.0, -0.26406, -0.24143, analog_pin, digital_pin, i2c, address
        )


class MQ138(MQSensor):
    """MQ-138: VOCs, toluene, acetone. Default coefficients for toluene."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_LINEAR, 1.0, -0.4434, 0.15397, analog_pin, digital_pin, i2c, address
        )


class MQ214(MQSensor):
    """MQ-214: methane, natural gas. No default coefficients - use setRegressionModel()."""

    def __init__(self, analog_pin=None, digital_pin=None, i2c=None, address=0x30):
        super().__init__(
            REGRESSION_LINEAR, 1.0, 0.0, 0.0, analog_pin, digital_pin, i2c, address
        )
