# FILE: max7219.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the MAX7219/MAX7221 LED matrix controller.
# LAST UPDATED: 2026-05-06

from machine import SPI, Pin
from os import uname
import time

# ---------------------------------------------------------------------------
# Module type constants
# Each module type sets different hardware mapping flags:
#   _hw_dig_rows  — MAX72xx digits map to rows (True) or columns (False)
#   _hw_rev_cols  — columns are reversed
#   _hw_rev_rows  — rows are reversed
# ---------------------------------------------------------------------------
GENERIC_HW    = 0   # DR0CR1RR0 — common cheap eBay modules
FC16_HW       = 1   # DR1CR0RR0 — FC-16 modules (4-in-1 sets)
PAROLA_HW     = 2   # DR1CR1RR0 — Parola custom modules
ICSTATION_HW  = 3   # DR1CR1RR1 — ICStation kit modules

DR0CR0RR0_HW  = 4
DR0CR0RR1_HW  = 5
DR0CR1RR0_HW  = 6   # same as GENERIC_HW
DR0CR1RR1_HW  = 7
DR1CR0RR0_HW  = 8   # same as FC16_HW
DR1CR0RR1_HW  = 9
DR1CR1RR0_HW  = 10  # same as PAROLA_HW
DR1CR1RR1_HW  = 11  # same as ICSTATION_HW

# Control request constants
SHUTDOWN   = 0
SCANLIMIT  = 1
INTENSITY  = 2
TEST       = 3
DECODE     = 4
UPDATE     = 10
WRAPAROUND = 11

# Control value constants
OFF = 0
ON  = 1

# Transform type constants
TSL  = 0   # Shift Left
TSR  = 1   # Shift Right
TSU  = 2   # Shift Up
TSD  = 3   # Shift Down
TFLR = 4   # Flip Left-Right
TFUD = 5   # Flip Up-Down
TRC  = 6   # Rotate Clockwise
TINV = 7   # Invert

# Display geometry
ROW_SIZE      = 8
COL_SIZE      = 8
MAX_INTENSITY = 0xF
MAX_SCANLIMIT = 7

# MAX72xx opcodes
OP_NOOP        = 0
OP_DIGIT0      = 1
OP_DECODEMODE  = 9
OP_INTENSITY   = 10
OP_SCANLIMIT   = 11
OP_SHUTDOWN    = 12
OP_DISPLAYTEST = 15

ALL_CHANGED = 0xFF
ALL_CLEAR   = 0x00

# Built-in 5x8 variable-width font (version 2 format, ASCII 0-255)
# Each entry: (width, col0, col1, ...) — stored as a flat bytearray
# Format header: 'F', version=2, firstASCII_hi, firstASCII_lo,
#                lastASCII_hi, lastASCII_lo, height
# Characters follow as: width_byte, col_bytes...
_SYSFONT = bytearray([
    ord('F'), 2, 0, 0, 0, 255, 8,
    0,                                         # 0
    5, 62, 91, 79, 91, 62,                     # 1
    5, 62, 107, 79, 107, 62,                   # 2
    5, 28, 62, 124, 62, 28,                    # 3
    5, 24, 60, 126, 60, 24,                    # 4
    5, 28, 87, 125, 87, 28,                    # 5
    5, 28, 94, 127, 94, 28,                    # 6
    4, 0, 24, 60, 24,                          # 7
    5, 255, 231, 195, 231, 255,                # 8
    4, 0, 24, 36, 24,                          # 9
    5, 255, 231, 219, 231, 255,                # 10
    5, 48, 72, 58, 6, 14,                      # 11
    5, 38, 41, 121, 41, 38,                    # 12
    5, 64, 127, 5, 5, 7,                       # 13
    5, 64, 127, 5, 37, 63,                     # 14
    5, 90, 60, 231, 60, 90,                    # 15
    5, 127, 62, 28, 28, 8,                     # 16
    5, 8, 28, 28, 62, 127,                     # 17
    5, 20, 34, 127, 34, 20,                    # 18
    5, 255, 255, 255, 255, 255,                # 19
    5, 240, 240, 240, 240, 240,                # 20
    3, 255, 255, 255,                          # 21
    5, 0, 0, 0, 255, 255,                      # 22
    5, 15, 15, 15, 15, 15,                     # 23
    5, 8, 4, 126, 4, 8,                        # 24
    5, 16, 32, 126, 32, 16,                    # 25
    5, 8, 8, 42, 28, 8,                        # 26
    5, 8, 28, 42, 8, 8,                        # 27
    5, 170, 0, 85, 0, 170,                     # 28
    5, 170, 85, 170, 85, 170,                  # 29
    5, 48, 56, 62, 56, 48,                     # 30
    5, 6, 14, 62, 14, 6,                       # 31
    2, 0, 0,                                   # 32 space
    1, 95,                                     # 33 !
    3, 7, 0, 7,                                # 34 "
    5, 20, 127, 20, 127, 20,                   # 35 #
    5, 68, 74, 255, 74, 50,                    # 36 $
    5, 99, 19, 8, 100, 99,                     # 37 %
    5, 54, 73, 73, 54, 72,                     # 38 &
    1, 7,                                      # 39 '
    3, 62, 65, 65,                             # 40 (
    3, 65, 65, 62,                             # 41 )
    5, 8, 42, 28, 42, 8,                       # 42 *
    5, 8, 8, 62, 8, 8,                         # 43 +
    2, 96, 224,                                # 44 ,
    4, 8, 8, 8, 8,                             # 45 -
    2, 96, 96,                                 # 46 .
    5, 96, 16, 8, 4, 3,                        # 47 /
    5, 62, 81, 73, 69, 62,                     # 48 0
    3, 4, 2, 127,                              # 49 1
    5, 113, 73, 73, 73, 70,                    # 50 2
    5, 65, 73, 73, 73, 54,                     # 51 3
    5, 15, 8, 8, 8, 127,                       # 52 4
    5, 79, 73, 73, 73, 49,                     # 53 5
    5, 62, 73, 73, 73, 48,                     # 54 6
    5, 3, 1, 1, 1, 127,                        # 55 7
    5, 54, 73, 73, 73, 54,                     # 56 8
    5, 6, 73, 73, 73, 62,                      # 57 9
    2, 108, 108,                               # 58 :
    2, 108, 236,                               # 59 ;
    3, 8, 20, 34,                              # 60 <
    4, 20, 20, 20, 20,                         # 61 =
    3, 34, 20, 8,                              # 62 >
    5, 1, 89, 9, 9, 6,                         # 63 ?
    5, 62, 65, 93, 89, 78,                     # 64 @
    5, 126, 9, 9, 9, 126,                      # 65 A
    5, 127, 73, 73, 73, 54,                    # 66 B
    5, 62, 65, 65, 65, 65,                     # 67 C
    5, 127, 65, 65, 65, 62,                    # 68 D
    5, 127, 73, 73, 73, 65,                    # 69 E
    5, 127, 9, 9, 9, 1,                        # 70 F
    5, 62, 65, 65, 73, 121,                    # 71 G
    5, 127, 8, 8, 8, 127,                      # 72 H
    3, 65, 127, 65,                            # 73 I
    5, 48, 65, 65, 65, 63,                     # 74 J
    5, 127, 8, 20, 34, 65,                     # 75 K
    5, 127, 64, 64, 64, 64,                    # 76 L
    5, 127, 2, 12, 2, 127,                     # 77 M
    5, 127, 4, 8, 16, 127,                     # 78 N
    5, 62, 65, 65, 65, 62,                     # 79 O
    5, 127, 9, 9, 9, 6,                        # 80 P
    5, 62, 65, 65, 97, 126,                    # 81 Q
    5, 127, 9, 25, 41, 70,                     # 82 R
    5, 70, 73, 73, 73, 49,                     # 83 S
    5, 1, 1, 127, 1, 1,                        # 84 T
    5, 63, 64, 64, 64, 63,                     # 85 U
    5, 31, 32, 64, 32, 31,                     # 86 V
    5, 63, 64, 56, 64, 63,                     # 87 W
    5, 99, 20, 8, 20, 99,                      # 88 X
    5, 3, 4, 120, 4, 3,                        # 89 Y
    5, 97, 81, 73, 69, 67,                     # 90 Z
    3, 127, 65, 65,                            # 91 [
    5, 3, 4, 8, 16, 96,                        # 92 backslash
    3, 65, 65, 127,                            # 93 ]
    5, 4, 2, 1, 2, 4,                          # 94 ^
    4, 128, 128, 128, 128,                     # 95 _
    3, 1, 2, 4,                                # 96 `
    4, 56, 68, 68, 124,                        # 97 a
    4, 127, 68, 68, 56,                        # 98 b
    4, 56, 68, 68, 68,                         # 99 c
    4, 56, 68, 68, 127,                        # 100 d
    4, 56, 84, 84, 88,                         # 101 e
    4, 4, 126, 5, 1,                           # 102 f
    4, 24, 164, 164, 124,                      # 103 g
    4, 127, 4, 4, 120,                         # 104 h
    1, 125,                                    # 105 i
    3, 132, 133, 124,                          # 106 j
    4, 127, 16, 40, 68,                        # 107 k
    1, 127,                                    # 108 l
    5, 124, 4, 120, 4, 120,                    # 109 m
    4, 124, 4, 4, 120,                         # 110 n
    4, 56, 68, 68, 56,                         # 111 o
    4, 252, 36, 36, 24,                        # 112 p
    4, 24, 36, 36, 252,                        # 113 q
    4, 124, 4, 4, 8,                           # 114 r
    4, 88, 84, 84, 52,                         # 115 s
    3, 4, 127, 4,                              # 116 t
    4, 60, 64, 64, 124,                        # 117 u
    4, 28, 32, 64, 124,                        # 118 v
    5, 60, 64, 48, 64, 60,                     # 119 w
    4, 108, 16, 16, 108,                       # 120 x
    4, 28, 160, 160, 124,                      # 121 y
    4, 100, 84, 84, 76,                        # 122 z
    4, 8, 54, 65, 65,                          # 123 {
    1, 127,                                    # 124 |
    4, 65, 65, 54, 8,                          # 125 }
    4, 2, 1, 2, 1,                             # 126 ~
    5, 127, 65, 65, 65, 127,                   # 127
])

# Characters 128-255 are left as zero-width (empty) in this compact table
# The font lookup will return 0 columns for anything above 127
_FONT_FIRST = 0
_FONT_LAST  = 127
_FONT_HEIGHT = 8
_FONT_DATA_OFFSET = 7  # bytes consumed by the header


def _font_char_offset(c):
    """Return the byte offset of character c in _SYSFONT, or -1 if not found."""
    if c < _FONT_FIRST or c > _FONT_LAST:
        return -1
    offset = _FONT_DATA_OFFSET
    for i in range(_FONT_FIRST, c):
        width = _SYSFONT[offset]
        offset += width + 1  # skip width byte + column data
    return offset


class MAX7219:
    """
    MicroPython class for the MAX7219/MAX7221 LED matrix controller.

    Supports single and chained 8x8 LED matrix modules. Communication
    is over hardware SPI. Pixel coordinate (0,0) is the top-right corner;
    column numbers increase leftward, row numbers increase downward.
    """

    def __init__(self, module_type, spi, cs_pin, num_devices=1):
        """
        Initialize the MAX72xx controller.

        :param module_type: One of the module type constants (e.g. FC16_HW, GENERIC_HW)
        :param spi:         Initialized machine.SPI object
        :param cs_pin:      machine.Pin object configured as output for chip select
        :param num_devices: Number of daisy-chained modules (default 1)
        """
        self._spi = spi
        self._cs  = cs_pin
        self._cs.value(1)

        self._max_devices   = num_devices
        self._update_enabled = True
        self._wrap_around    = False

        # Per-device buffers: list of dicts with 'dig' (bytearray[8]) and 'changed' (int)
        self._matrix = [
            {'dig': bytearray(ROW_SIZE), 'changed': ALL_CLEAR}
            for _ in range(num_devices)
        ]

        # SPI send buffer: 2 bytes per device (opcode + data)
        self._spi_data = bytearray(num_devices * 2)

        # Set hardware mapping flags based on module type
        self._set_module_parameters(module_type)

        # Initialize the MAX72xx hardware
        self._send_control(OP_DISPLAYTEST, 0)                  # no test
        self._send_control(OP_SCANLIMIT, ROW_SIZE - 1)         # show all rows
        self._send_control(OP_INTENSITY, MAX_INTENSITY // 2)   # medium brightness
        self._send_control(OP_DECODEMODE, 0)                   # no BCD decode
        self.clear()
        self._send_control(OP_SHUTDOWN, 1)                     # normal operation

    # -------------------------------------------------------------------------
    # Hardware mapping
    # -------------------------------------------------------------------------

    def _set_module_parameters(self, mod):
        """Configure internal flags based on module hardware type."""
        if mod in (DR0CR0RR0_HW,):
            self._hw_dig_rows = False; self._hw_rev_cols = False; self._hw_rev_rows = False
        elif mod in (DR0CR0RR1_HW,):
            self._hw_dig_rows = False; self._hw_rev_cols = False; self._hw_rev_rows = True
        elif mod in (DR0CR1RR0_HW, GENERIC_HW):
            self._hw_dig_rows = False; self._hw_rev_cols = True;  self._hw_rev_rows = False
        elif mod in (DR0CR1RR1_HW,):
            self._hw_dig_rows = False; self._hw_rev_cols = True;  self._hw_rev_rows = True
        elif mod in (DR1CR0RR0_HW, FC16_HW):
            self._hw_dig_rows = True;  self._hw_rev_cols = False; self._hw_rev_rows = False
        elif mod in (DR1CR0RR1_HW,):
            self._hw_dig_rows = True;  self._hw_rev_cols = False; self._hw_rev_rows = True
        elif mod in (DR1CR1RR0_HW, PAROLA_HW):
            self._hw_dig_rows = True;  self._hw_rev_cols = True;  self._hw_rev_rows = False
        elif mod in (DR1CR1RR1_HW, ICSTATION_HW):
            self._hw_dig_rows = True;  self._hw_rev_cols = True;  self._hw_rev_rows = True
        else:
            # Default to GENERIC if unknown
            self._hw_dig_rows = False; self._hw_rev_cols = True;  self._hw_rev_rows = False

    def _hw_row(self, r):
        return (ROW_SIZE - 1 - r) if self._hw_rev_rows else r

    def _hw_col(self, c):
        return (COL_SIZE - 1 - c) if self._hw_rev_cols else c

    # -------------------------------------------------------------------------
    # SPI communication
    # -------------------------------------------------------------------------

    def _spi_clear(self):
        """Fill the SPI buffer with NOOPs."""
        for i in range(len(self._spi_data)):
            self._spi_data[i] = OP_NOOP

    def _spi_offset(self, dev, x):
        """Return the byte index in _spi_data for device dev, byte x (0=opcode, 1=data)."""
        return ((self._max_devices - 1 - dev) * 2) + x

    def _spi_send(self):
        """Shift out the SPI buffer to all chained devices."""
        self._cs.value(0)
        self._spi.write(self._spi_data)
        self._cs.value(1)

    def _send_control(self, opcode, value):
        """Send the same opcode+value to every device in the chain."""
        self._spi_clear()
        for dev in range(self._max_devices):
            self._spi_data[self._spi_offset(dev, 0)] = opcode
            self._spi_data[self._spi_offset(dev, 1)] = value & 0xFF
        self._spi_send()

    # -------------------------------------------------------------------------
    # Buffer flush
    # -------------------------------------------------------------------------

    def _flush_buffer(self, buf):
        """Send any changed rows for a single device to the hardware."""
        if buf >= self._max_devices:
            return
        for i in range(ROW_SIZE):
            if self._matrix[buf]['changed'] & (1 << i):
                self._spi_clear()
                row_data = self._matrix[buf]['dig'][i]
                # Rotate bit 0 to bit 7 (hardware requirement)
                lsb = row_data & 1
                row_data = ((row_data >> 1) | (lsb << 7)) & 0xFF
                self._spi_data[self._spi_offset(buf, 0)] = OP_DIGIT0 + i
                self._spi_data[self._spi_offset(buf, 1)] = row_data
                self._spi_send()
        self._matrix[buf]['changed'] = ALL_CLEAR

    def _flush_buffer_all(self):
        """Send all changed rows for all devices, row by row for efficiency."""
        for i in range(ROW_SIZE):
            changed = False
            self._spi_clear()
            for dev in range(self._max_devices):
                if self._matrix[dev]['changed'] & (1 << i):
                    row_data = self._matrix[dev]['dig'][i]
                    lsb = row_data & 1
                    row_data = ((row_data >> 1) | (lsb << 7)) & 0xFF
                    self._spi_data[self._spi_offset(dev, 0)] = OP_DIGIT0 + i
                    self._spi_data[self._spi_offset(dev, 1)] = row_data
                    changed = True
            if changed:
                self._spi_send()
        for dev in range(self._max_devices):
            self._matrix[dev]['changed'] = ALL_CLEAR

    # -------------------------------------------------------------------------
    # Control
    # -------------------------------------------------------------------------

    def control(self, mode, value, start_dev=None, end_dev=None):
        """
        Set a control parameter for one or all devices.

        :param mode:      One of the control constants (SHUTDOWN, INTENSITY, etc.)
        :param value:     ON/OFF or a numeric value
        :param start_dev: First device index (optional, default all)
        :param end_dev:   Last device index (optional, default all)
        """
        if start_dev is None:
            start_dev = 0
        if end_dev is None:
            end_dev = self._max_devices - 1

        if mode == UPDATE:
            self._update_enabled = (value == ON)
            if self._update_enabled:
                self._flush_buffer_all()
            return

        if mode == WRAPAROUND:
            self._wrap_around = (value == ON)
            return

        # Map to hardware opcode
        if mode == SHUTDOWN:
            opcode = OP_SHUTDOWN
            param  = 0 if value == ON else 1   # 0=shutdown, 1=normal
        elif mode == SCANLIMIT:
            opcode = OP_SCANLIMIT
            param  = min(value, MAX_SCANLIMIT)
        elif mode == INTENSITY:
            opcode = OP_INTENSITY
            param  = min(value, MAX_INTENSITY)
        elif mode == DECODE:
            opcode = OP_DECODEMODE
            param  = 0xFF if value == ON else 0
        elif mode == TEST:
            opcode = OP_DISPLAYTEST
            param  = 1 if value == ON else 0
        else:
            return

        self._spi_clear()
        for dev in range(start_dev, end_dev + 1):
            self._spi_data[self._spi_offset(dev, 0)] = opcode
            self._spi_data[self._spi_offset(dev, 1)] = param
        self._spi_send()

    def setIntensity(self, intensity, dev=None):
        """
        Set LED brightness.

        :param intensity: Value 0-15
        :param dev:       Device index, or None for all devices
        """
        if dev is None:
            self.control(INTENSITY, intensity)
        else:
            self.control(INTENSITY, intensity, dev, dev)

    def getDeviceCount(self):
        """:return: Number of devices in the chain."""
        return self._max_devices

    def getColumnCount(self):
        """:return: Total number of columns across all devices."""
        return self._max_devices * COL_SIZE

    # -------------------------------------------------------------------------
    # Clear
    # -------------------------------------------------------------------------

    def clear(self, start_dev=None, end_dev=None):
        """
        Clear all LEDs in one or all devices.

        :param start_dev: First device (default 0)
        :param end_dev:   Last device (default last)
        """
        if start_dev is None:
            start_dev = 0
        if end_dev is None:
            end_dev = self._max_devices - 1
        for buf in range(start_dev, end_dev + 1):
            for i in range(ROW_SIZE):
                self._matrix[buf]['dig'][i] = 0
            self._matrix[buf]['changed'] = ALL_CHANGED
        if self._update_enabled:
            self._flush_buffer_all()

    # -------------------------------------------------------------------------
    # Row and column access
    # -------------------------------------------------------------------------

    def _bit_reverse(self, b):
        """Reverse the bit order of a byte."""
        b = ((b & 0xF0) >> 4) | ((b & 0x0F) << 4)
        b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2)
        b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1)
        return b & 0xFF

    def getRow(self, buf, r):
        """
        Read the LED state for a row in a device buffer.

        :param buf: Device index
        :param r:   Row [0..7]
        :return:    Byte with one bit per LED
        """
        if buf >= self._max_devices or r >= ROW_SIZE:
            return 0
        if self._hw_dig_rows:
            v = self._matrix[buf]['dig'][self._hw_row(r)]
            return self._bit_reverse(v) if self._hw_rev_cols else v
        else:
            # dig entries represent columns; assemble the row from each column bit
            mask = 1 << self._hw_col(r)
            value = 0
            for i in range(COL_SIZE):
                if self._matrix[buf]['dig'][self._hw_row(i)] & mask:
                    value |= (1 << i)
            return value

    def setRow(self, buf, r, value):
        """
        Set all LEDs in a row of a device.

        :param buf:   Device index
        :param r:     Row [0..7]
        :param value: Byte bitmask — bit N on = LED N lit
        :return: True on success
        """
        if buf >= self._max_devices or r >= ROW_SIZE:
            return False
        if self._hw_dig_rows:
            self._matrix[buf]['dig'][self._hw_row(r)] = (
                self._bit_reverse(value) if self._hw_rev_cols else value
            ) & 0xFF
            self._matrix[buf]['changed'] |= (1 << self._hw_row(r))
        else:
            mask = 1 << self._hw_col(r)
            for i in range(ROW_SIZE):
                if value & (1 << i):
                    self._matrix[buf]['dig'][self._hw_row(i)] |= mask
                else:
                    self._matrix[buf]['dig'][self._hw_row(i)] &= ~mask & 0xFF
            self._matrix[buf]['changed'] = ALL_CHANGED
        if self._update_enabled:
            self._flush_buffer(buf)
        return True

    def getColumn(self, buf, c=None):
        """
        Read the LED state for a column.

        Can be called as getColumn(absolute_col) or getColumn(buf, col_within_buf).
        """
        if c is None:
            # absolute column mode
            abs_col = buf
            buf = abs_col // COL_SIZE
            c   = abs_col % COL_SIZE
        if buf >= self._max_devices or c >= COL_SIZE:
            return 0
        if self._hw_dig_rows:
            mask = 1 << self._hw_col(c)
            value = 0
            for i in range(ROW_SIZE):
                if self._matrix[buf]['dig'][self._hw_row(i)] & mask:
                    value |= (1 << i)
            return value
        else:
            v = self._matrix[buf]['dig'][self._hw_row(c)]
            return self._bit_reverse(v) if self._hw_rev_cols else v

    def setColumn(self, buf, c=None, value=None):
        """
        Set all LEDs in a column.

        Can be called as setColumn(absolute_col, value) or setColumn(buf, col, value).
        """
        if value is None:
            # two-argument absolute mode: setColumn(abs_col, value)
            abs_col = buf
            value   = c
            buf     = abs_col // COL_SIZE
            c       = abs_col % COL_SIZE
        if buf >= self._max_devices or c >= COL_SIZE:
            return False
        if self._hw_dig_rows:
            mask = 1 << self._hw_col(c)
            for i in range(ROW_SIZE):
                if value & (1 << i):
                    self._matrix[buf]['dig'][self._hw_row(i)] |= mask
                else:
                    self._matrix[buf]['dig'][self._hw_row(i)] &= ~mask & 0xFF
            self._matrix[buf]['changed'] = ALL_CHANGED
        else:
            self._matrix[buf]['dig'][self._hw_row(c)] = (
                self._bit_reverse(value) if self._hw_rev_cols else value
            ) & 0xFF
            self._matrix[buf]['changed'] |= (1 << self._hw_row(c))
        if self._update_enabled:
            self._flush_buffer(buf)
        return True

    # -------------------------------------------------------------------------
    # Pixel access
    # -------------------------------------------------------------------------

    def getPoint(self, r, c):
        """
        Read a single LED state.

        :param r: Row [0..7]
        :param c: Absolute column [0..getColumnCount()-1]
        :return:  True if LED is on
        """
        buf   = c // COL_SIZE
        c_loc = c % COL_SIZE
        if buf >= self._max_devices or r >= ROW_SIZE or c_loc >= COL_SIZE:
            return False
        if self._hw_dig_rows:
            return bool(self._matrix[buf]['dig'][self._hw_row(r)] & (1 << self._hw_col(c_loc)))
        else:
            return bool(self._matrix[buf]['dig'][self._hw_row(c_loc)] & (1 << self._hw_col(r)))

    def setPoint(self, r, c, state):
        """
        Set a single LED on or off.

        :param r:     Row [0..7]
        :param c:     Absolute column [0..getColumnCount()-1]
        :param state: True = on, False = off
        :return: True on success
        """
        buf   = c // COL_SIZE
        c_loc = c % COL_SIZE
        if buf >= self._max_devices or r >= ROW_SIZE or c_loc >= COL_SIZE:
            return False
        if self._hw_dig_rows:
            row_hw = self._hw_row(r)
            col_hw = self._hw_col(c_loc)
            if state:
                self._matrix[buf]['dig'][row_hw] |= (1 << col_hw)
            else:
                self._matrix[buf]['dig'][row_hw] &= ~(1 << col_hw) & 0xFF
            self._matrix[buf]['changed'] |= (1 << row_hw)
        else:
            row_hw = self._hw_row(c_loc)
            col_hw = self._hw_col(r)
            if state:
                self._matrix[buf]['dig'][row_hw] |= (1 << col_hw)
            else:
                self._matrix[buf]['dig'][row_hw] &= ~(1 << col_hw) & 0xFF
            self._matrix[buf]['changed'] |= (1 << row_hw)
        if self._update_enabled:
            self._flush_buffer(buf)
        return True

    # -------------------------------------------------------------------------
    # Buffer block operations
    # -------------------------------------------------------------------------

    def getBuffer(self, col, size):
        """
        Read a block of column data starting at col.

        :param col:  Starting absolute column
        :param size: Number of columns to read
        :return:     bytearray of column values, or None on error
        """
        if col >= self.getColumnCount():
            return None
        result = bytearray(size)
        for i in range(size):
            result[i] = self.getColumn(col - i) if col >= 0 else 0
            col -= 1
        return result

    def setBuffer(self, col, data):
        """
        Write a block of column data starting at col.

        :param col:  Starting absolute column
        :param data: Iterable of column byte values
        :return: True on success
        """
        if col >= self.getColumnCount():
            return False
        old_update = self._update_enabled
        self._update_enabled = False
        for v in data:
            self.setColumn(col, v)
            col -= 1
        self._update_enabled = old_update
        if self._update_enabled:
            self._flush_buffer_all()
        return True

    # -------------------------------------------------------------------------
    # Update control
    # -------------------------------------------------------------------------

    def update(self, buf=None):
        """
        Force an update to the hardware.

        :param buf: Device index to update, or None for all devices.
        """
        if buf is None:
            self._flush_buffer_all()
        else:
            self._flush_buffer(buf)

    def setUpdate(self, on):
        """Enable or disable auto-updates after every change."""
        self.control(UPDATE, ON if on else OFF)

    def setWraparound(self, on):
        """Enable or disable column wrap-around during shifts."""
        self.control(WRAPAROUND, ON if on else OFF)

    # -------------------------------------------------------------------------
    # Transforms
    # -------------------------------------------------------------------------

    def transform(self, ttype, start_dev=None, end_dev=None):
        """
        Apply a transformation to all (or a range of) device buffers.

        :param ttype:     One of TSL, TSR, TSU, TSD, TFLR, TFUD, TRC, TINV
        :param start_dev: First device (default 0)
        :param end_dev:   Last device (default last)
        :return: True on success
        """
        if start_dev is None:
            start_dev = 0
        if end_dev is None:
            end_dev = self._max_devices - 1

        old_update = self._update_enabled
        self._update_enabled = False

        if ttype == TSL:
            col_data = self.getColumn(end_dev, COL_SIZE - 1) if self._wrap_around else 0
            for buf in range(end_dev, start_dev - 1, -1):
                self._transform_buffer(buf, ttype)
                next_col = self.getColumn(buf - 1, COL_SIZE - 1) if buf > start_dev else col_data
                self.setColumn(buf, 0, next_col)
            self.setColumn(start_dev, 0, col_data)

        elif ttype == TSR:
            col_data = self.getColumn(start_dev, 0) if self._wrap_around else 0
            for buf in range(start_dev, end_dev + 1):
                self._transform_buffer(buf, ttype)
                next_col = self.getColumn(buf + 1, 0) if buf < end_dev else col_data
                self.setColumn(buf, COL_SIZE - 1, next_col)
            self.setColumn(end_dev, COL_SIZE - 1, col_data)

        elif ttype == TFLR:
            # Reverse device order then reverse columns within each device
            devs = list(range(start_dev, end_dev + 1))
            for i in range(len(devs) // 2):
                a, b = devs[i], devs[-(i + 1)]
                self._matrix[a], self._matrix[b] = self._matrix[b], self._matrix[a]
            for buf in range(start_dev, end_dev + 1):
                self._transform_buffer(buf, ttype)

        else:
            for buf in range(start_dev, end_dev + 1):
                self._transform_buffer(buf, ttype)

        self._update_enabled = old_update
        if self._update_enabled:
            self._flush_buffer_all()
        return True

    def _transform_buffer(self, buf, ttype):
        """Apply a transformation to one device buffer in place."""
        m = self._matrix[buf]['dig']

        if ttype == TSL:
            for i in range(ROW_SIZE):
                if self._hw_rev_cols:
                    m[i] = (m[i] >> 1) & 0xFF
                else:
                    m[i] = (m[i] << 1) & 0xFF

        elif ttype == TSR:
            for i in range(ROW_SIZE):
                if self._hw_rev_cols:
                    m[i] = (m[i] << 1) & 0xFF
                else:
                    m[i] = (m[i] >> 1) & 0xFF

        elif ttype == TSU:
            t = self.getRow(buf, 0) if self._wrap_around else 0
            if self._hw_dig_rows:
                for i in range(ROW_SIZE - 1):
                    m[i] = m[i + 1]
            else:
                for i in range(ROW_SIZE - 1, -1, -1):
                    m[i] = (m[i] << 1) & 0xFF
            self.setRow(buf, ROW_SIZE - 1, t)

        elif ttype == TSD:
            t = self.getRow(buf, ROW_SIZE - 1) if self._wrap_around else 0
            if self._hw_dig_rows:
                for i in range(ROW_SIZE - 1, 0, -1):
                    m[i] = m[i - 1]
            else:
                for i in range(ROW_SIZE):
                    m[i] = (m[i] >> 1) & 0xFF
            self.setRow(buf, 0, t)

        elif ttype == TFLR:
            if self._hw_dig_rows:
                for i in range(ROW_SIZE):
                    m[i] = self._bit_reverse(m[i])
            else:
                for i in range(ROW_SIZE // 2):
                    m[i], m[ROW_SIZE - 1 - i] = m[ROW_SIZE - 1 - i], m[i]

        elif ttype == TFUD:
            if self._hw_dig_rows:
                for i in range(ROW_SIZE // 2):
                    m[i], m[ROW_SIZE - 1 - i] = m[ROW_SIZE - 1 - i], m[i]
            else:
                for i in range(ROW_SIZE):
                    m[i] = self._bit_reverse(m[i])

        elif ttype == TRC:
            t = [self.getColumn(buf, COL_SIZE - 1 - i) for i in range(ROW_SIZE)]
            for i in range(ROW_SIZE):
                self.setRow(buf, i, t[i])

        elif ttype == TINV:
            for i in range(ROW_SIZE):
                m[i] = (~m[i]) & 0xFF

        self._matrix[buf]['changed'] = ALL_CHANGED

    # -------------------------------------------------------------------------
    # Font / character rendering
    # -------------------------------------------------------------------------

    def getChar(self, c, max_size=8):
        """
        Retrieve the column bitmap data for a character from the built-in font.

        :param c:        Character code (int or single-char string)
        :param max_size: Maximum number of columns to return
        :return:         bytearray of column data, empty if not found
        """
        if isinstance(c, str):
            c = ord(c)
        offset = _font_char_offset(c)
        if offset == -1:
            return bytearray()
        width = _SYSFONT[offset]
        size  = min(max_size, width)
        return bytearray(_SYSFONT[offset + 1: offset + 1 + size])

    def setChar(self, col, c):
        """
        Render a character from the built-in font at the given absolute column.
        Columns are filled right-to-left (col, col-1, col-2, ...).

        :param col: Rightmost absolute column for the character
        :param c:   Character to display (int or single-char string)
        :return:    Width in columns of the character, 0 if not found
        """
        if isinstance(c, str):
            c = ord(c)
        offset = _font_char_offset(c)
        if offset == -1:
            return 0
        width = _SYSFONT[offset]
        old_update = self._update_enabled
        self._update_enabled = False
        for i in range(width):
            col_data = _SYSFONT[offset + 1 + i]
            self.setColumn(col - i, col_data)
        self._update_enabled = old_update
        if self._update_enabled:
            self._flush_buffer_all()
        return width

    def printText(self, text, col=None):
        """
        Render a string on the display, right-to-left starting at col.

        :param text: String to display
        :param col:  Starting column (default = rightmost column of last device)
        """
        if col is None:
            col = self.getColumnCount() - 1
        old_update = self._update_enabled
        self._update_enabled = False
        for ch in text:
            width = self.setChar(col, ch)
            col -= width + 1  # one blank column gap between characters
        self._update_enabled = old_update
        if self._update_enabled:
            self._flush_buffer_all()

    def scrollText(self, text, delay_ms=50, blank_cols=1):
        """
        Scroll a text string across the display from right to left.

        :param text:       String to scroll
        :param delay_ms:   Milliseconds between each column shift
        :param blank_cols: Number of blank columns between characters (default 1)
        """
        # Build the full pixel column data for the message
        columns = []
        for ch in text:
            data = self.getChar(ch)
            columns.extend(data)
            columns.extend([0] * blank_cols)  # gap between characters

        # Pad with blank columns so the text fully scrolls off the left
        columns.extend([0] * self.getColumnCount())

        # Scroll by shifting one column at a time
        col_count = self.getColumnCount()
        for start in range(len(columns)):
            old_update = self._update_enabled
            self._update_enabled = False
            col = col_count - 1
            for i in range(col_count):
                src_idx = start + i
                v = columns[src_idx] if src_idx < len(columns) else 0
                self.setColumn(col, v)
                col -= 1
            self._update_enabled = old_update
            self._flush_buffer_all()
            time.sleep_ms(delay_ms)