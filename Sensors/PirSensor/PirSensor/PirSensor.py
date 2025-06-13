# FILE: PirSensor.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython module for the PIR movement sensor
# LAST UPDATED: 2025-05-23
from machine import Pin
from Qwiic import Qwiic
import struct


class PIRSensor(Qwiic):
    def __init__(self, i2c=None, address=0x30, pin=None):
        """
        Initializes the PIRSensor.

        :param i2c: I2C object (required for Qwiic mode)
        :param address: I2C address (default 0x30)
        :param pin: GPIO pin number for native mode. If provided, native mode is used.
        """
        if pin is not None:
            # Native mode
            super().__init__(i2c=None, native=True)
            self.pin = Pin(pin, Pin.IN)
        else:
            # I2C mode
            super().__init__(i2c=i2c, address=address, native=False)
        self.state = False
        self.delay_time = 2  # Default delay time in seconds

    def initialize_native(self):
        """
        Setup for native GPIO input.
        """
        # Already initialized in __init__
        pass

    def set_delay(self, delay_time_sec: int):
        """
        Set the delay time the PIR output stays HIGH after being triggered.

        :param delay_time_sec: Delay time in seconds
        """
        self.delay_time = delay_time_sec
        data = struct.pack("<I", self.delay_time)
        self.send_data(data)

    def get_state(self) -> bool:
        """
        Returns the current state of the PIR sensor.
        """
        if self.native:
            self.state = bool(self.pin.value())
        else:
            data = self.read_data(1)
            self.state = bool(data[0]) if data else False
        return self.state

    def available(self) -> bool:
        """
        Check if the PIR sensor is responding on the I2C bus.
        """
        try:
            self.i2c.writeto(self.address, b"")
            return True
        except Exception:
            return False
