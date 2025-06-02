# FILE: lcdI2C.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython library for the I2C controlled 16x2 LCD display
# LAST UPDATED: 2025-05-23
from machine import I2C
from time import sleep_ms, sleep_us


class LCDOutput:
    """Helper class to manage the control and data signals sent to the I2C LCD driver."""

    def __init__(self):
        # Control and data signal bits
        self.rs = 0  # Register select: 0 = command, 1 = data
        self.rw = 0  # Read/write: 0 = write, 1 = read (usually 0)
        self.E = 0  # Enable signal
        self.Led = 0  # Backlight control
        self.data = 0  # 8-bit data value

    def get_high_data(self):
        """Return high nibble of data combined with control bits for transmission."""
        return (
            (self.data & 0xF0)
            | (self.rs << 0)
            | (self.rw << 1)
            | (self.E << 2)
            | (self.Led << 3)
        )

    def get_low_data(self):
        """Return low nibble of data (shifted) combined with control bits for transmission."""
        return (
            ((self.data & 0x0F) << 4)
            | (self.rs << 0)
            | (self.rw << 1)
            | (self.E << 2)
            | (self.Led << 3)
        )


class LCD_I2C:
    """Class for controlling a character LCD via an I2C I/O expander"""

    def __init__(self, i2c: I2C, address=0x20):
        self.i2c = i2c
        self._address = address
        self._output = LCDOutput()
        self._entryState = 0b10  # Left-to-right text entry mode
        self._displayState = 0b100  # Display ON, cursor OFF, blink OFF

    def begin(self, beginWire=True):
        """Initialize the LCD. Optionally sends initial configuration to I2C registers."""
        if beginWire:
            self._i2c_write(3, 0x00)  # Configuration register
            sleep_ms(10)
            self._i2c_write(2, 0x00)  # Polarity register
            sleep_ms(10)
            self._i2c_write(1, 0x00)  # Output register
            sleep_ms(10)
        self.initialize_lcd()

    def _i2c_write(self, reg, value):
        """Write a value to a specific I2C register."""
        self.i2c.writeto(self._address, bytes([reg, value]))

    def i2c_write_data(self, value):
        """Write a raw byte to the I2C output register (LCD expander)."""
        self.i2c.writeto(self._address, bytes([1, value]))

    def lcd_write(self, value, initialization=False):
        """Send a byte to the LCD (as command or data depending on rs)."""
        self._output.data = value
        self._output.E = 1
        self.i2c_write_data(self._output.get_high_data())
        sleep_us(1)
        self._output.E = 0
        self.i2c_write_data(self._output.get_high_data())

        if not initialization:
            sleep_us(37)
            self._output.E = 1
            self.i2c_write_data(self._output.get_low_data())
            sleep_us(1)
            self._output.E = 0
            self.i2c_write_data(self._output.get_low_data())

    def initialize_lcd(self):
        """Perform the initialization sequence for the LCD in 4-bit mode."""
        self._output.rs = 0
        self._output.rw = 0

        # Initialization sequence (as per HD44780 datasheet)
        for val, delay in [
            (0b00110000, 4200),
            (0b00110000, 150),
            (0b00110000, 37),
            (0b00100000, 37),
        ]:
            self.lcd_write(val, initialization=True)
            sleep_us(delay)

        self.lcd_write(0b00101000)  # Function set: 4-bit, 2-line, 5x8 dots
        sleep_us(37)

        self.display()
        self.clear()
        self.leftToRight()

    def clear(self):
        """Clear the display and return cursor to home position."""
        self._output.rs = 0
        self._output.rw = 0
        self.lcd_write(0x01)
        sleep_us(1600)

    def home(self):
        """Return cursor to home position without clearing display."""
        self._output.rs = 0
        self._output.rw = 0
        self.lcd_write(0x02)
        sleep_us(1600)

    def leftToRight(self):
        """Set text entry to left-to-right mode."""
        self._entryState |= 1 << 1
        self._update_entry_mode()

    def rightToLeft(self):
        """Set text entry to right-to-left mode."""
        self._entryState &= ~(1 << 1)
        self._update_entry_mode()

    def autoscroll(self):
        """Enable automatic display shift during entry."""
        self._entryState |= 1
        self._update_entry_mode()

    def autoscrollOff(self):
        """Disable automatic display shift during entry."""
        self._entryState &= ~1
        self._update_entry_mode()

    def _update_entry_mode(self):
        """Apply current entry mode setting to the LCD."""
        self._output.rs = 0
        self._output.rw = 0
        self.lcd_write(0x04 | self._entryState)
        sleep_us(37)

    def display(self):
        """Turn on the display."""
        self._displayState |= 1 << 2
        self._update_display_control()

    def displayOff(self):
        """Turn off the display."""
        self._displayState &= ~(1 << 2)
        self._update_display_control()

    def cursorOn(self):
        """Show the cursor."""
        self._displayState |= 1 << 1
        self._update_display_control()

    def cursorOff(self):
        """Hide the cursor."""
        self._displayState &= ~(1 << 1)
        self._update_display_control()

    def blink(self):
        """Enable blinking cursor."""
        self._displayState |= 1
        self._update_display_control()

    def no_blink(self):
        """Disable blinking cursor."""
        self._displayState &= ~1
        self._update_display_control()

    def _update_display_control(self):
        """Apply current display control settings to the LCD."""
        self._output.rs = 0
        self._output.rw = 0
        self.lcd_write(0x08 | self._displayState)
        sleep_us(37)

    def scrollDisplayLeft(self):
        """Scroll the entire display one position to the left."""
        self.lcd_write(0x18)
        sleep_us(37)

    def scroll_display_right(self):
        """Scroll the entire display one position to the right."""
        self.lcd_write(0x1C)
        sleep_us(37)

    def createChar(self, location, charmap):
        """
        Create a custom character in CGRAM.
        `location` is 0-7, `charmap` is a list of 8 bytes (5 bits each).
        """
        location %= 8
        self._output.rs = 0
        self._output.rw = 0
        self.lcd_write(0x40 | (location << 3))
        sleep_us(37)
        for byte in charmap:
            self.write(byte)
        self.setcursorOn(0, 0)

    def setcursorOn(self, col, row):
        """Set the cursor to the specified column and row."""
        addr = 0x00 if row == 0 else 0x40
        addr += col
        self._output.rs = 0
        self._output.rw = 0
        self.lcd_write(0x80 | addr)
        sleep_us(37)

    def write(self, char):
        """Write a character to the display (accepts byte value)."""
        self._output.rs = 1
        self._output.rw = 0
        self.lcd_write(char)
        sleep_us(41)
        return 1

    def backlight(self):
        """Turn on the LCD backlight."""
        self._output.Led = 1
        self.i2c_write_data(0x00 | (self._output.Led << 3))

    def noBacklight(self):
        """Turn off the LCD backlight."""
        self._output.Led = 0
        self.i2c_write_data(0x00 | (self._output.Led << 3))

    def print(self, string):
        """Print a string to the LCD."""
        for char in string:
            self.write(ord(char))
