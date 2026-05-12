# FILE: inputronic_grid.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython driver for the Soldered Inputronic GRID 4x4 button+LED pad.
#        Communicates over I2C with the ATtiny firmware on the device.
# WORKS WITH: Inputronic GRID: www.soldered.com
# LAST UPDATED: 2026-05-12

from machine import I2C, Pin
from os import uname

INPUTRONIC_GRID_DEFAULT_ADDR = 0x30

_CMD_SET_LED      = 0x01  # Set one LED: [ledIdx, R, G, B]
_CMD_SET_ALL_LEDS = 0x02  # Set all LEDs to same color: [R, G, B]
_CMD_GET_BUTTON   = 0x03  # Query single button state: [buttonIdx]
_CMD_GET_ALL_PADS = 0x04  # Query all button states
_CMD_SET_ADDR     = 0x05  # Write new I2C address to EEPROM: [newAddr]
_CMD_SET_LED_MASK = 0x06  # Set LEDs by bitmask: [maskHi, maskLo, R, G, B]


class InputronicGrid:
    """
    MicroPython driver for the Soldered Inputronic GRID 4x4 button+LED pad.

    Usage:
        from machine import I2C, Pin
        from inputronic_grid import InputronicGrid

        i2c = I2C(0, scl=Pin(22), sda=Pin(21))
        grid = InputronicGrid(i2c=i2c)
        pressed = grid.readPad(0, 0)
        grid.setLED(0, 0, 255, 0, 0)
    """

    def __init__(self, i2c=None, address=INPUTRONIC_GRID_DEFAULT_ADDR):
        """
        Initialize the Inputronic GRID.

        :param i2c:     Initialized I2C object (auto-detected on known boards if None)
        :param address: I2C address of the device (default 0x30)
        """
        if i2c is not None:
            self._i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self._i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, pass an initialized I2C object")

        self._addr = address

        # Probe device
        try:
            self._i2c.writeto(self._addr, b"")
        except OSError:
            raise Exception("Inputronic GRID not found. Check wiring.")

    # ── Button reading ────────────────────────────────────────────────────────

    def readPad(self, row, col):
        """
        Read the state of a single pad by grid position.

        :param row: Row index, 0-3 (top to bottom)
        :param col: Column index, 0-3 (left to right)
        :return: True if pad is pressed
        """
        return self.readButton(self._idx(row, col))

    def readButton(self, index):
        """
        Read the state of a single button by flat index (row-major: index = row*4 + col).

        :param index: Button index, 0-15
        :return: True if button is pressed
        """
        if index >= 16:
            return False
        try:
            self._i2c.writeto(self._addr, bytes([_CMD_GET_BUTTON, index]))
            data = self._i2c.readfrom(self._addr, 1)
            return data[0] != 0
        except OSError:
            return False

    def readAllPads(self):
        """
        Read the state of all 16 pads in one I2C transaction.

        :return: 16-bit bitmask of pressed buttons; bit i corresponds to button i
        """
        try:
            self._i2c.writeto(self._addr, bytes([_CMD_GET_ALL_PADS]))
            data = self._i2c.readfrom(self._addr, 2)
            return (data[0] << 8) | data[1]
        except OSError:
            return 0

    # ── LED control ───────────────────────────────────────────────────────────

    def setLED(self, row, col, r, g, b, intensity=128):
        """
        Set one LED color by grid position.

        :param row:       Row index, 0-3
        :param col:       Column index, 0-3
        :param r:         Red component (0-255)
        :param g:         Green component (0-255)
        :param b:         Blue component (0-255)
        :param intensity: Brightness scale (0=off, 255=full, default 128)
        """
        self.setLEDByIndex(self._ledIdx(row, col), r, g, b, intensity)

    def setLEDByIndex(self, index, r, g, b, intensity=128):
        """
        Set one LED color by flat index.

        :param index:     LED index, 0-15
        :param r:         Red component (0-255)
        :param g:         Green component (0-255)
        :param b:         Blue component (0-255)
        :param intensity: Brightness scale (0=off, 255=full, default 128)
        """
        if index >= 16:
            return
        try:
            self._i2c.writeto(self._addr, bytes([
                _CMD_SET_LED,
                index,
                self._scale(r, intensity),
                self._scale(g, intensity),
                self._scale(b, intensity),
            ]))
        except OSError:
            pass

    def setAllLEDs(self, r, g, b):
        """
        Set all 16 LEDs to the same color.

        :param r: Red component (0-255)
        :param g: Green component (0-255)
        :param b: Blue component (0-255)
        """
        try:
            self._i2c.writeto(self._addr, bytes([_CMD_SET_ALL_LEDS, r, g, b]))
        except OSError:
            pass

    def setLEDMask(self, mask, r, g, b):
        """
        Set LEDs by bitmask. Only masked LEDs receive the color; others turn off.

        :param mask: 16-bit bitmask of LEDs to light (bit i = LED i)
        :param r:    Red component (0-255)
        :param g:    Green component (0-255)
        :param b:    Blue component (0-255)
        """
        try:
            self._i2c.writeto(self._addr, bytes([
                _CMD_SET_LED_MASK,
                (mask >> 8) & 0xFF,
                mask & 0xFF,
                r, g, b,
            ]))
        except OSError:
            pass

    def clearLEDs(self):
        """Turn all LEDs off."""
        self.setAllLEDs(0, 0, 0)

    # ── Address change ────────────────────────────────────────────────────────

    def setAddress(self, newAddr):
        """
        Change the device I2C address, persist to EEPROM, and re-initialize.
        Device is available on new address within ~1 ms. Ignored if newAddr
        is outside valid 7-bit I2C range (0x08-0x77).

        :param newAddr: New I2C address (0x08-0x77)
        """
        if newAddr < 0x08 or newAddr > 0x77:
            return
        try:
            self._i2c.writeto(self._addr, bytes([_CMD_SET_ADDR, newAddr]))
        except OSError:
            pass
        self._addr = newAddr

    # ── Private helpers ───────────────────────────────────────────────────────

    def _idx(self, row, col):
        return row * 4 + col

    def _ledIdx(self, row, col):
        # Serpentine: even rows left→right, odd rows right→left
        return (row * 4 + col) if (row % 2 == 0) else (row * 4 + (3 - col))

    def _scale(self, value, intensity):
        return (value * intensity) // 255
