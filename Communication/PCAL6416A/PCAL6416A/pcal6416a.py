# FILE: pcal6416a.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the PCAL6416A 16-bit IO expander
# LAST UPDATED: 2026-04-23

from machine import I2C, Pin
from os import uname

# I2C address (ADDR pin low = 0x20, ADDR pin high = 0x21)
PCAL6416A_I2C_ADDR = 0x20

# Register addresses
PCAL6416A_INPORT0        = 0x00  # Input port 0
PCAL6416A_INPORT1        = 0x01  # Input port 1
PCAL6416A_OUTPORT0       = 0x02  # Output port 0
PCAL6416A_OUTPORT1       = 0x03  # Output port 1
PCAL6416A_POLINVPORT0    = 0x04  # Polarity inversion port 0
PCAL6416A_POLINVPORT1    = 0x05  # Polarity inversion port 1
PCAL6416A_CFGPORT0       = 0x06  # Configuration port 0 (1=input, 0=output)
PCAL6416A_CFGPORT1       = 0x07  # Configuration port 1
PCAL6416A_OUTDRVST_REG00 = 0x40  # Output drive strength port A, pins 0-3 (2 bits/pin)
PCAL6416A_OUTDRVST_REG01 = 0x41  # Output drive strength port A, pins 4-7
PCAL6416A_OUTDRVST_REG10 = 0x42  # Output drive strength port B, pins 0-3
PCAL6416A_OUTDRVST_REG11 = 0x43  # Output drive strength port B, pins 4-7
PCAL6416A_INLAT_REG0     = 0x44  # Input latch register 0
PCAL6416A_INLAT_REG1     = 0x45  # Input latch register 1
PCAL6416A_PUPDEN_REG0    = 0x46  # Pull-up/pull-down enable register 0
PCAL6416A_PUPDEN_REG1    = 0x47  # Pull-up/pull-down enable register 1
PCAL6416A_PUPDSEL_REG0   = 0x48  # Pull-up/pull-down selection register 0 (1=pull-up)
PCAL6416A_PUPDSEL_REG1   = 0x49  # Pull-up/pull-down selection register 1
PCAL6416A_INTMSK_REG0    = 0x4A  # Interrupt mask register 0 (0=enabled, 1=masked)
PCAL6416A_INTMSK_REG1    = 0x4B  # Interrupt mask register 1
PCAL6416A_INTSTAT_REG0   = 0x4C  # Interrupt status register 0 (cleared on read)
PCAL6416A_INTSTAT_REG1   = 0x4D  # Interrupt status register 1
PCAL6416A_OUTPORT_CONF   = 0x4F  # Output port configuration (0=push-pull, 1=open-drain per port)

# Pin name aliases — port A = pins 0-7, port B = pins 8-15
PCAL6416A_A0 = 0
PCAL6416A_A1 = 1
PCAL6416A_A2 = 2
PCAL6416A_A3 = 3
PCAL6416A_A4 = 4
PCAL6416A_A5 = 5
PCAL6416A_A6 = 6
PCAL6416A_A7 = 7
PCAL6416A_B0 = 8
PCAL6416A_B1 = 9
PCAL6416A_B2 = 10
PCAL6416A_B3 = 11
PCAL6416A_B4 = 12
PCAL6416A_B5 = 13
PCAL6416A_B6 = 14
PCAL6416A_B7 = 15

# Pin modes
INPUT          = 0
OUTPUT         = 1
INPUT_PULLUP   = 2
INPUT_PULLDOWN = 3


class PCAL6416A:
    """
    MicroPython class for the PCAL6416A 16-bit GPIO expander.
    Supports 16 GPIO pins across two 8-bit ports (A0-A7, B0-B7).
    """

    def __init__(self, i2c=None, address=PCAL6416A_I2C_ADDR):
        """
        Initialize the PCAL6416A expander.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address of the device (default 0x20)
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.address = address

        # Shadow registers mirror the chip state to avoid unnecessary reads
        # Power-on reset defaults from PCAL6416A datasheet
        self._cfg     = [0xFF, 0xFF]             # Configuration: all inputs
        self._out     = [0xFF, 0xFF]             # Output: all high
        self._pol     = [0x00, 0x00]             # Polarity: no inversion
        self._pupden  = [0x00, 0x00]             # Pull enable: all disabled
        self._pupdsel = [0xFF, 0xFF]             # Pull selection: all pull-up
        self._drvst   = [0xFF, 0xFF, 0xFF, 0xFF] # Drive strength: strongest
        self._intmsk  = [0xFF, 0xFF]             # Interrupt mask: all masked
        self._inlat   = [0x00, 0x00]             # Input latch: disabled
        self._outconf = 0x00                     # Output config: push-pull

    def _readByte(self, reg):
        try:
            data = self.i2c.readfrom_mem(self.address, reg, 1)
            return True, data[0]
        except:
            return False, 0

    def _writeByte(self, reg, val):
        try:
            self.i2c.writeto_mem(self.address, reg, bytes([val]))
            return True
        except:
            return False

    def pinMode(self, pin, mode):
        """
        Configure a pin's direction and optional pull resistor.

        :param pin: Pin number 0-15 (use PCAL6416A_A0..A7 or PCAL6416A_B0..B7 aliases)
        :param mode: INPUT, OUTPUT, INPUT_PULLUP, or INPUT_PULLDOWN
        """
        if pin > 15:
            return
        port = pin // 8
        bit  = pin % 8

        if mode == INPUT:
            self._cfg[port] |= (1 << bit)
            self._writeByte(PCAL6416A_CFGPORT0 + port, self._cfg[port])

        elif mode == OUTPUT:
            self._cfg[port] &= ~(1 << bit)
            self._out[port] &= ~(1 << bit)
            self._writeByte(PCAL6416A_OUTPORT0 + port, self._out[port])
            self._writeByte(PCAL6416A_CFGPORT0 + port, self._cfg[port])

        elif mode == INPUT_PULLUP:
            self._cfg[port]    |= (1 << bit)
            self._pupden[port] |= (1 << bit)
            self._pupdsel[port] |= (1 << bit)
            self._writeByte(PCAL6416A_CFGPORT0     + port, self._cfg[port])
            self._writeByte(PCAL6416A_PUPDEN_REG0  + port, self._pupden[port])
            self._writeByte(PCAL6416A_PUPDSEL_REG0 + port, self._pupdsel[port])

        elif mode == INPUT_PULLDOWN:
            self._cfg[port]    |= (1 << bit)
            self._pupden[port] |= (1 << bit)
            self._pupdsel[port] &= ~(1 << bit)
            self._writeByte(PCAL6416A_CFGPORT0     + port, self._cfg[port])
            self._writeByte(PCAL6416A_PUPDEN_REG0  + port, self._pupden[port])
            self._writeByte(PCAL6416A_PUPDSEL_REG0 + port, self._pupdsel[port])

    def digitalWrite(self, pin, state):
        """
        Set the output level on a pin configured as OUTPUT.

        :param pin: Pin number 0-15
        :param state: 0 (LOW) or 1 (HIGH)
        """
        if pin > 15:
            return
        state &= 1
        port = pin // 8
        bit  = pin % 8

        if state:
            self._out[port] |= (1 << bit)
        else:
            self._out[port] &= ~(1 << bit)
        self._writeByte(PCAL6416A_OUTPORT0 + port, self._out[port])

    def digitalRead(self, pin):
        """
        Read the current logic level of a pin.

        :param pin: Pin number 0-15
        :return: 0 (LOW) or 1 (HIGH), or -1 for invalid pin or I2C error
        """
        if pin > 15:
            return -1
        port = pin // 8
        bit  = pin % 8

        ok, val = self._readByte(PCAL6416A_INPORT0 + port)
        if not ok:
            return -1
        return (val >> bit) & 1

    def pinPolarity(self, pin, state):
        """
        Invert the polarity of an input pin (reads as opposite of actual level).

        :param pin: Pin number 0-15
        :param state: 1 to invert, 0 for normal polarity
        """
        if pin > 15:
            return
        state &= 1
        port = pin // 8
        bit  = pin % 8

        if state:
            self._pol[port] |= (1 << bit)
        else:
            self._pol[port] &= ~(1 << bit)
        self._writeByte(PCAL6416A_POLINVPORT0 + port, self._pol[port])

    def driveStrength(self, pin, strength):
        """
        Set the output drive strength for a pin.

        Each pin has a 2-bit drive strength field: 0 = weakest, 3 = strongest.

        :param pin: Pin number 0-15
        :param strength: 0 to 3
        """
        if pin > 15:
            return
        reg     = pin // 4          # which of the four drive-strength registers
        bit_pos = (pin % 4) * 2     # 2 bits per pin within that register
        strength &= 3

        self._drvst[reg] &= ~(3 << bit_pos)
        self._drvst[reg] |=  (strength << bit_pos)
        self._writeByte(PCAL6416A_OUTDRVST_REG00 + reg, self._drvst[reg])

    def setInterrupt(self, pin, enable):
        """
        Enable or disable change-detection interrupt for a pin.

        The INT pin goes low when an unmasked input changes state.

        :param pin: Pin number 0-15
        :param enable: True to enable interrupt, False to mask it
        """
        if pin > 15:
            return
        port = pin // 8
        bit  = pin % 8

        # Interrupt mask register: 0 = interrupt enabled, 1 = masked
        if enable:
            self._intmsk[port] &= ~(1 << bit)
        else:
            self._intmsk[port] |=  (1 << bit)
        self._writeByte(PCAL6416A_INTMSK_REG0 + port, self._intmsk[port])

    def getInterrupts(self):
        """
        Read the interrupt status flags. The register clears automatically on read.

        :return: 16-bit value — bit N is set if pin N triggered an interrupt
        """
        ok0, low  = self._readByte(PCAL6416A_INTSTAT_REG0)
        ok1, high = self._readByte(PCAL6416A_INTSTAT_REG1)
        if not ok0 or not ok1:
            return 0
        return (high << 8) | low

    def inputLatching(self, pin, enable):
        """
        Enable input latching on a pin so that brief pulses are held until read.

        :param pin: Pin number 0-15
        :param enable: True to enable latching, False to disable
        """
        if pin > 15:
            return
        port = pin // 8
        bit  = pin % 8

        if enable:
            self._inlat[port] |= (1 << bit)
        else:
            self._inlat[port] &= ~(1 << bit)
        self._writeByte(PCAL6416A_INLAT_REG0 + port, self._inlat[port])

    def openDrainPort(self, port, enable):
        """
        Configure an entire port as open-drain (requires external pull-up) or push-pull.

        :param port: 0 for port A, 1 for port B
        :param enable: True for open-drain, False for push-pull
        """
        port &= 1
        if enable:
            self._outconf |= (1 << port)
        else:
            self._outconf &= ~(1 << port)
        self._writeByte(PCAL6416A_OUTPORT_CONF, self._outconf)
