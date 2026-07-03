# FILE: ButtonLedBuzzerBoard.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the Soldered Button, LED & Buzzer Board with Qwiic
# LAST UPDATED: 2026-05-20

from machine import I2C, Pin
from os import uname

# Default I2C address
BLB_DEFAULT_ADDRESS = 0x30

# Register addresses
BLB_REG_BUTTONS = 0x00
BLB_REG_LED = 0x01
BLB_REG_BUZZER = 0x02

# Number of LEDs
BLB_NUM_LEDS = 3


class ButtonLedBuzzerBoard:
    """
    MicroPython class for the Soldered Button, LED & Buzzer Board (ATtiny404).
    Communicates over I2C.
    """

    def __init__(self, i2c=None, address=BLB_DEFAULT_ADDRESS):
        """
        Initialize the ButtonLedBuzzerBoard.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address of the device (default 0x30)
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            elif uname().sysname == "esp8266":
                self.i2c = I2C(scl=Pin(5), sda=Pin(4))
            else:
                raise Exception(
                    "Board not recognized, please pass an I2C object manually"
                )

        self.address = address
        self._led_buf = bytearray(BLB_NUM_LEDS * 3)

    def _writeLEDs(self):
        try:
            self.i2c.writeto(self.address, bytes([BLB_REG_LED]) + bytes(self._led_buf))
        except:
            pass

    def setLED(self, index, r, g, b):
        """Set single LED by index (0-2) to given RGB color."""
        if index >= BLB_NUM_LEDS:
            return
        self._led_buf[index * 3] = r
        self._led_buf[index * 3 + 1] = g
        self._led_buf[index * 3 + 2] = b
        self._writeLEDs()

    def setAllLEDs(self, r, g, b):
        """Set all LEDs to same RGB color."""
        for i in range(BLB_NUM_LEDS):
            self._led_buf[i * 3] = r
            self._led_buf[i * 3 + 1] = g
            self._led_buf[i * 3 + 2] = b
        self._writeLEDs()

    def setLEDs(self, r1, g1, b1, r2, g2, b2, r3, g3, b3):
        """Set all three LEDs to individual RGB colors."""
        self._led_buf[0] = r1
        self._led_buf[1] = g1
        self._led_buf[2] = b1
        self._led_buf[3] = r2
        self._led_buf[4] = g2
        self._led_buf[5] = b2
        self._led_buf[6] = r3
        self._led_buf[7] = g3
        self._led_buf[8] = b3
        self._writeLEDs()

    def setBuzzer(self, freq):
        """Set buzzer frequency in Hz. Pass 0 to turn off."""
        try:
            self.i2c.writeto(
                self.address, bytes([BLB_REG_BUZZER, (freq >> 8) & 0xFF, freq & 0xFF])
            )
        except:
            pass

    def readButtons(self):
        """Read raw button state byte. Bit0=BTN1, Bit1=BTN2, Bit2=BTN3."""
        try:
            self.i2c.writeto(self.address, bytes([BLB_REG_BUTTONS]))
            data = self.i2c.readfrom(self.address, 1)
            return data[0]
        except:
            return 0

    def isButton1Pressed(self):
        """Return True if button 1 is pressed."""
        return bool(self.readButtons() & 0x01)

    def isButton2Pressed(self):
        """Return True if button 2 is pressed."""
        return bool(self.readButtons() & 0x02)

    def isButton3Pressed(self):
        """Return True if button 3 is pressed."""
        return bool(self.readButtons() & 0x04)
