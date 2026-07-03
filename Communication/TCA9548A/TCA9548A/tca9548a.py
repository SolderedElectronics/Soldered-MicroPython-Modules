# FILE: tca9548a.py
# AUTHOR: Ported to MicroPython — styled after pcal6416a.py by Fran Fodor @ Soldered
# BRIEF: MicroPython library for the TCA9548A 8-channel I2C multiplexer
# LAST UPDATED: 2026-04-30

from machine import I2C, Pin
from os import uname

# I2C address (A0/A1/A2 pins set bits 0-2 of the address)
TCA9548A_I2C_ADDR = 0x70  # Default: A0=A1=A2=GND

# Channel bitmasks for writeRegister()
TCA_CHANNEL_0 = 0x01
TCA_CHANNEL_1 = 0x02
TCA_CHANNEL_2 = 0x04
TCA_CHANNEL_3 = 0x08
TCA_CHANNEL_4 = 0x10
TCA_CHANNEL_5 = 0x20
TCA_CHANNEL_6 = 0x40
TCA_CHANNEL_7 = 0x80


class TCA9548A:
    """
    MicroPython class for the TCA9548A 8-channel I2C multiplexer.
    Connects one I2C master to up to 8 downstream I2C buses via channel selection.
    """

    def __init__(self, i2c=None, address=TCA9548A_I2C_ADDR):
        """
        Initialize the TCA9548A multiplexer.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address of the device (default 0x70)
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.address = address

        # Shadow register mirrors the chip's channel control byte
        # Power-on reset default: all channels disabled
        self._channels = 0x00

    def _writeByte(self, val):
        try:
            self.i2c.writeto(self.address, bytes([val]))
            return True
        except:
            return False

    def _readByte(self):
        try:
            data = self.i2c.readfrom(self.address, 1)
            return True, data[0]
        except:
            return False, 0

    def openChannel(self, channel):
        """
        Connect a downstream channel to the upstream I2C bus.
        Multiple channels can be open simultaneously.

        :param channel: Channel number 0-7
        """
        if channel > 7:
            return
        self._channels |= 1 << channel
        self._writeByte(self._channels)

    def closeChannel(self, channel):
        """
        Disconnect a downstream channel from the upstream I2C bus.

        :param channel: Channel number 0-7
        """
        if channel > 7:
            return
        self._channels ^= 1 << channel
        self._writeByte(self._channels)

    def closeAll(self):
        """
        Disconnect all downstream channels from the upstream I2C bus.
        """
        self._channels = 0x00
        self._writeByte(self._channels)

    def openAll(self):
        """
        Connect all downstream channels to the upstream I2C bus simultaneously.
        """
        self._channels = 0xFF
        self._writeByte(self._channels)

    def writeRegister(self, value):
        """
        Directly write a value to the TCA9548A channel control register.
        Each bit corresponds to one channel (bit 0 = channel 0, etc.).

        :param value: 8-bit bitmask of channels to enable (use TCA_CHANNEL_x constants)
        """
        self._channels = value
        self._writeByte(self._channels)

    def readRegister(self):
        """
        Read the current state of the TCA9548A channel control register.

        :return: 8-bit channel bitmask, or 255 on I2C error
        """
        ok, val = self._readByte()
        if not ok:
            return 255
        return val
