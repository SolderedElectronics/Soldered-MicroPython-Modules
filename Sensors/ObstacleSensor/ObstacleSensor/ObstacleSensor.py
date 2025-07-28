# FILE: ObstacleSensor.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: A MicroPython module for the Qwiic and native versions of the Obstacle Sensor breakout
# LAST UPDATED: 2025-06-18

from os import uname
from Qwiic import Qwiic
from machine import Pin, I2C, ADC

READ_ADDRESS = 0  # Address/register from which to read analog data via I2C


class ObstacleSensor(Qwiic):
    def __init__(self, i2c=None, address=0x30, digital_pin=None, analog_pin=None):
        """
        Initializes the ObstacleSensor object.

        The sensor can operate in two modes:
        - Native GPIO mode using analog and/or digital pins.
        - I2C mode using the Qwiic interface.

        Args:
            i2c (I2C, optional): An I2C instance to use for communication in I2C mode.
            address (int): I2C address of the sensor (default 0x30).
            digital_pin (int, optional): GPIO pin number for digital input.
            analog_pin (int, optional): GPIO pin number for analog input.
        """
        if analog_pin is not None:
            # Initialize analog pin using ADC
            self.analog_pin = ADC(Pin(analog_pin))
            self.native = True  # Use native GPIO mode

        if digital_pin is not None:
            # Initialize digital pin
            self.digital_pin = Pin(digital_pin, Pin.OUT)
            self.native = True  # Use native GPIO mode

        if analog_pin is None and digital_pin is None:
            # No GPIO pins provided; fall back to I2C mode
            if i2c is not None:
                # Use provided I2C interface
                i2c = i2c
            else:
                # Auto-configure I2C for known board types (e.g., ESP32, ESP8266)
                if uname().sysname in (
                    "esp32",
                    "esp8266",
                    "Soldered Dasduino CONNECTPLUS",
                ):
                    i2c = I2C(0, scl=Pin(22), sda=Pin(21))  # Default Qwiic pins
                else:
                    raise Exception("Board not recognized, enter I2C pins manually")

            # Call parent constructor to initialize I2C connection
            super().__init__(i2c=i2c, address=address, native=False)

    def analogRead(self):
        """
        Reads the analog value from the sensor.

        Returns:
            int: Analog sensor reading
        """
        if self.native:
            # Read directly from the analog pin in native mode
            return self.analog_pin.read()
        else:
            # Read 2 bytes from I2C and convert to integer
            data = self.read_register(READ_ADDRESS, 2)
            value = data[0] << 8 | data[1]
            return value

    def setTreshold(self, value: int):
        """
        Sets the obstacle detection threshold (only in I2C mode).

        Args:
            value (int): Threshold value (0–1023).

        Raises:
            Exception: If value is out of range or used in native mode.
        """
        if not self.native:
            if value > 1023 or value < 0:
                raise Exception("Treshold value should be between 0 and 1023!")
            data = [0x02, 0, 0]  # Command format: 0x02 + 2 bytes for threshold
            data[1] = (value & 0xFF00) >> 8  # MSB
            data[2] = value & 0xFF  # LSB
            self.treshold = value
            self.send_data(data)

    def getTreshold(self):
        """
        Returns the currently set threshold value.

        Returns:
            int: Threshold value.
        """
        return self.treshold

    def digitalRead(self):
        """
        Reads the digital output from the sensor.

        Returns:
            int: 0 or 1 indicating presence or absence of an obstacle.

        Note:
            - In native mode, reads directly from the GPIO pin.
            - In I2C mode, performs analogRead and compares to threshold.
        """
        if self.native:
            return self.digital_pin.value()
        else:
            return (
                self.analogRead() < self.treshold
            )  # Compare analog value to threshold
