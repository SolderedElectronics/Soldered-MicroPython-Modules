# FILE: UltrasonicSensor.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: A MicroPython module for the HC-SR04 UltraSonic sensor. Supports both the Native and Qwiic version
# LAST UPDATED: 2025-06-12


# Import Qwiic base class for I2C devices
from Qwiic import Qwiic

# Import Pin and I2C classes for GPIO and I2C operations
from machine import I2C, Pin

# Used to detect the board type (ESP32, ESP8266, etc.)
from os import uname

# Time module used for precise delays and measuring pulse duration
import time

# Register addresses for I2C communication with a supported ultrasonic module
TAKE_MEAS_REG = 0  # Command register to start measurement
DISTANCE_REG = 1  # Register where distance in cm is stored (from external sensor)
DURATION_REG = 2  # Register where echo pulse duration is stored (from external sensor)


class UltrasonicSensor(Qwiic):
    """
    Ultrasonic sensor class that supports both native (GPIO) and I2C-based operation.
    In native mode, it uses GPIO pins to trigger and read echo.
    In I2C mode, it uses a pre-programmed I2C-based ultrasonic sensor.
    """

    def __init__(self, i2c=None, address=0x30, echo_pin=None, trig_pin=None):
        """
        Initializes the sensor either in native GPIO mode or I2C mode.
        - If trig_pin and echo_pin are given: use GPIO mode.
        - Otherwise, fall back to I2C mode.
        """
        if trig_pin is not None and echo_pin is not None:
            # Native GPIO mode: setup trig and echo pins
            self.trig_pin = Pin(trig_pin, Pin.OUT)
            self.echo_pin = Pin(echo_pin, Pin.IN)
            self.native = True
        else:
            # I2C mode
            if i2c is not None:
                # Use provided I2C instance
                i2c = i2c
            else:
                # Auto-select Qwiic for CONNECT boards
                if uname().sysname in ("esp32", "esp8266"):
                    i2c = I2C(0, scl=Pin(22), sda=Pin(21))
                else:
                    raise Exception("Board not recognized, enter I2C pins manually")
            # Call the Qwiic base class constructor
            super().__init__(i2c=i2c, address=address, native=False)

    def takeMeasure(self):
        """
        For I2C mode: Sends a command to start measurement on the I2C sensor.
        """
        return self.send_address(TAKE_MEAS_REG)

    def _measure_pulse(self, timeout_us=50000):
        """
        Manual pulse-in implementation to measure echo pulse width in microseconds.
        Waits for the echo pin to go high, then times how long it stays high.
        If the pulse is not received within timeout, returns 0.
        """
        start = time.ticks_us()

        # Wait for echo pin to go high (start of echo)
        while self.echo_pin.value() == 0:
            if time.ticks_diff(time.ticks_us(), start) > timeout_us:
                return 0  # Timeout occurred

        pulse_start = time.ticks_us()

        # Wait for echo pin to go low (end of echo)
        while self.echo_pin.value() == 1:
            if time.ticks_diff(time.ticks_us(), pulse_start) > timeout_us:
                return 0  # Timeout occurred

        pulse_end = time.ticks_us()
        duration = time.ticks_diff(pulse_end, pulse_start)
        return duration  # Return pulse width in microseconds

    def getDuration(self):
        """
        Returns the duration (in microseconds) of the echo signal.
        - In native mode: triggers a measurement and measures echo duration using GPIO.
        - In I2C mode: reads duration from external sensor over I2C.
        """
        if self.native:
            # Trigger a short pulse to start measurement
            self.trig_pin.value(0)
            time.sleep_us(5)
            self.trig_pin.value(1)
            time.sleep_us(20)
            self.trig_pin.value(0)

            # Measure echo pulse width
            return self._measure_pulse()
        else:
            # Read duration from I2C register
            data = self.read_register(DURATION_REG, 2)
            return data[1] << 8 | data[0]

    def getDistance(self):
        """
        Returns the distance to an object in centimeters.
        - In native mode: measures pulse duration and calculates distance using speed of sound.
        - In I2C mode: reads precomputed distance from external sensor over I2C.
        """
        if self.native:
            # Trigger pulse
            self.trig_pin.value(0)
            time.sleep_us(5)
            self.trig_pin.value(1)
            time.sleep_us(20)
            self.trig_pin.value(0)

            # Measure pulse width
            duration = self._measure_pulse()

            # Convert duration to distance (speed of sound = 0.034 cm/us)
            distance_cm = duration * 0.034 / 2.0  # divide by 2 (round trip)
            return distance_cm
        else:
            # Read distance from I2C register
            data = self.read_register(DISTANCE_REG, 2)
            return data[1] << 8 | data[0]
