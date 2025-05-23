# FILE: Qwiic.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython module for Qwiic functionalities
# LAST UPDATED: 2025-05-23
from machine import I2C
import time
from os import uname

class Qwiic:
    
    def __init__(self, i2c=None, address: int = 0x30, native: bool = False):
        """
        Initialize the Qwiic interface.

        :param i2c: Initialized machine.I2C object
        :param address: I2C address of the device
        :param native: Use native initialization instead of I2C
        """
        if i2c != None:
            self.i2c = i2c
        else:
            if uname().sysname == "esp32":
                print("Ude ovdje")
                self.i2c=I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter Qwiic I2C pins manually")
        self.address = address
        self.native = native
        self.begin_done = False
        self.err = 0

    def begin(self):
        """
        Initializes the sensor using native or I2C.
        """
        if self.native:
            self.initialize_native()
        else:
            # No action needed for MicroPython, assume i2c is already initialized
            pass
        self.begin_done = True

    def initialize_native(self):
        """
        Override this method in subclasses if native initialization is required.
        """
        raise NotImplementedError("Subclasses must implement initialize_native()")

    def send_address(self, reg_addr: int) -> int:
        """
        Sends a single byte (register address) to the device.
        """
        try:
            self.i2c.writeto(self.address, bytes([reg_addr]))
            return 0
        except Exception as e:
            self.err = e
            return -1

    def read_data(self, n: int) -> bytes:
        """
        Reads `n` bytes from the device.
        """
        try:
            return self.i2c.readfrom(self.address, n)
        except Exception as e:
            self.err = e
            return bytes()

    def read_register(self, reg_addr: int, n: int) -> bytes:
        """
        Sends a register address, then reads `n` bytes from the device.
        """
        if self.send_address(reg_addr) != 0:
            return bytes()
        return self.read_data(n)

    def send_data(self, data: bytes) -> int:
        """
        Writes data to the device.
        """
        try:
            self.i2c.writeto(self.address, data)
            return 0
        except Exception as e:
            self.err = e
            return -1
            return -1
