# FILE: Relay.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the Soldered Relay board with Qwiic/I2C
# LAST UPDATED: 2026-05-21

from machine import I2C, Pin
from os import uname

# Default I2C address
RELAY_DEFAULT_ADDRESS = 0x30

# Relay channels
CHANNEL1 = 0
CHANNEL2 = 1
CHANNEL3 = 2
CHANNEL4 = 8


class Relay:
    """
    MicroPython class for the Soldered Relay board (Qwiic/I2C version).
    Supports 1, 2, and 4 channel relay boards.
    Communicates over I2C.
    """

    def __init__(self, i2c=None, address=RELAY_DEFAULT_ADDRESS):
        """
        Initialize the Relay board.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address of the device (default 0x30, range 0x30-0x37)
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            elif uname().sysname == "esp8266":
                self.i2c = I2C(scl=Pin(5), sda=Pin(4))
            else:
                raise Exception("Board not recognized, please pass an I2C object manually")

        self.address = address
        self._channelState = [0, 0, 0, 0]

    def relayControl(self, channel, mode):
        """
        Turn a relay channel on or off.

        :param channel: CHANNEL1, CHANNEL2, CHANNEL3, or CHANNEL4
        :param mode: 1 to turn on, 0 to turn off
        """
        try:
            self.i2c.writeto(self.address, bytes([channel, mode]))
        except:
            pass
        self._setChannelState(channel, mode)

    def getChannelState(self, channel):
        """Return the last set state of a relay channel (1=on, 0=off)."""
        return self._channelState[3 if channel == CHANNEL4 else channel]

    def _setChannelState(self, channel, mode):
        self._channelState[3 if channel == CHANNEL4 else channel] = mode
