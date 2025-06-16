# FILE: RotaryEncoder.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: A MicroPython module for the Qwiic version of the Rotary Encoder
# LAST UPDATED: 2025-06-16 

from os import uname
from Qwiic import Qwiic
from machine import Pin, I2C
import ustruct

# Constants representing possible encoder states or events
ROTARY_IDLE = 0             # No action
BTN_CLICK = 1               # Single button press
BTN_DOUBLE_CLICK = 2        # Two quick button presses
BTN_LONG_PRESS = 3          # Button held down
BTN_LONG_RELEASE = 4        # Release after long press
ROTARY_CCW = 5              # Counter-clockwise rotation
ROTARY_CW = 6               # Clockwise rotation

# The address of the register that stores encoder data
REGISTER_ADDRESS = 0

# RotaryEncoder class inheriting from Qwiic for I2C communication
class RotaryEncoder(Qwiic):

    def __init__(self, i2c=None, address=0x30):
        """
        Initializes the RotaryEncoder object.
        
        If no I2C bus is provided, it attempts to initialize the default
        I2C bus on ESP32 or ESP8266 boards using GPIO pins 22 (SCL) and 21 (SDA).
        """
        if i2c != None:
            i2c = i2c  # Use provided I2C interface
        else:
            # Auto-select I2C pins for supported boards
            if uname().sysname == "esp32" or uname().sysname == "esp8266":
                i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        # Call superclass constructor with selected I2C interface and I2C address
        super().__init__(i2c=i2c, address=address, native=False)

    def getData(self):
        """
        Reads 5 bytes of data from the encoder and unpacks:
        - 4 bytes for the rotary count
        - 1 byte for the encoder/button state
        """
        data = self.read_register(REGISTER_ADDRESS, 5)

        # First 2 bytes: little-endian signed integer for encoder position
        self.rotaryCount = (ustruct.unpack('<h', data))[0]

        # Fifth byte (index 4) holds the encoder or button event state
        self.state = data[4]

    def getCount(self):
        """
        Returns the current rotary encoder count.
        """
        self.getData()
        return self.rotaryCount

    def getState(self):
        """
        Returns the current state of the encoder or button press event.
        Can be one of the ROTARY_* or BTN_* constants.
        """
        self.getData()
        return self.state

    def resetCount(self):
        """
        Sends a reset command to the rotary encoder to clear the count value.
        """
        self.send_data(bytes([190]))  # Command to trigger count reset
        self.send_address(0xAA)       # Likely required to complete/reset the command