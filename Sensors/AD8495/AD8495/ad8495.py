# FILE: AD8495.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: A MicroPython module for the AD8495 Thermocouple amplifier
# LAST UPDATED: 2025-07-02 

from machine import ADC, Pin

class AD8495:
    """
    MicroPython driver for the AD8495 thermocouple amplifier.
    Assumes analog output is connected to an ADC-capable pin.
    """

    def __init__(self, pin, resolution_bits=12, reference_voltage=3.3):
        """
        Initialize the AD8495 sensor.

        Args:
            pin (int or str): ADC-capable pin (e.g., 32 on Dasduino CONECTPLUS or 'A0' on Dasduino CORE).
            resolution_bits (int): ADC resolution in bits (default 12-bit = 4096 steps).
            reference_voltage (float): Reference voltage for ADC (typically 3.3V).
        """
        self._adc = ADC(Pin(pin))
        self._resolution = 2**resolution_bits-1
        self._vref = reference_voltage
        self._voltage_offset_constant = 2.4 if reference_voltage == 3.3 else 1.65
        self._lsb = self._vref / self._resolution
        self._offset = 0.0
        self._deg_per_mv = 1.0 / 0.005  # 5 mV/°C

    def setTemperatureOffset(self, offset):
        """Set temperature offset in °C."""
        self._offset = offset

    def getTemperatureOffset(self):
        """Get current temperature offset in °C."""
        return self._offset

    def getPrecision(self):
        """Return ADC LSB in volts."""
        return self._lsb

    def readVoltage(self, samples=1):
        """
        Read the voltage from the ADC.

        Args:
            samples (int): Number of samples to average (default 1).

        Returns:
            float: Averaged voltage in volts.
        """
        samples = max(samples, 1)
        total = 0
        for _ in range(samples):
            total += self._adc.read()
        avg_raw = total / samples
        return avg_raw * self._lsb

    def getTemperatureC(self, samples=1):
        """
        Get temperature in Celsius.

        Args:
            samples (int): Number of ADC samples to average.

        Returns:
            float: Temperature in °C.
        """
        voltage = self.readVoltage(samples)
        temp_c = (voltage - self._voltage_offset_constant) / 0.005
        return temp_c + self._offset


    def getTemperatureF(self, samples=1):
        """
        Get temperature in Fahrenheit.

        Args:
            samples (int): Number of ADC samples to average.

        Returns:
            float: Temperature in °F.
        """
        return self.getTemperatureC(samples) * 1.8 + 32.0


    def getSetpointVoltage(self, temperature_c):
        """
        Convert a temperature in Celsius to the equivalent voltage output by the sensor.

        Args:
            temperature_c (float): Temperature in °C.

        Returns:
            float: Equivalent voltage in volts.
        """
        return temperature_c / self._deg_per_mv
    
    def setVoltageOffset(self, newOffset):
        """
        Set the offset voltage used to calculate temperature
        
        Args:
            newOffset (float): Offset in Volts
            
        """
        self._voltage_offset_constant = newOffset