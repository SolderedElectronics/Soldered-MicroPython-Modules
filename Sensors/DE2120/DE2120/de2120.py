# FILE: de2120.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the DE2120 2D Barcode Scanner Engine
# LAST UPDATED: 2026-04-23

from machine import UART
import time

# ACK / NACK bytes returned by the module after a command
DE2120_COMMAND_ACK = 0x06
DE2120_COMMAND_NACK = 0x15

# Commands (sent as ^_^<cmd><arg>.)
COMMAND_START_SCAN = "SCAN"
COMMAND_STOP_SCAN = "SLEEP"
COMMAND_SET_DEFAULTS = "DEFALT"
COMMAND_GET_VERSION = "DSPYFW"

# Configurable properties
PROPERTY_BUZZER_FREQ = "BEPPWM"
# BEPPWM0 - Active Drive
# BEPPWM1 - Passive Low Freq
# BEPPWM2 - Passive Med Freq (default)
# BEPPWM3 - Passive Hi Freq

PROPERTY_DECODE_BEEP = "BEPSUC"
# BEPSUC1 - ON (default)  BEPSUC0 - OFF

PROPERTY_BOOT_BEEP = "BEPPWR"
# BEPPWR1 - ON (default)  BEPPWR0 - OFF

PROPERTY_FLASH_LIGHT = "LAMENA"
# LAMENA1 - ON (default)  LAMENA0 - OFF

PROPERTY_AIM_LIGHT = "AIMENA"
# AIMENA1 - ON (default)  AIMENA0 - OFF

PROPERTY_READING_AREA = "IMGREG"
# IMGREG0 - Full (default)  IMGREG1 - 80%  IMGREG2 - 60%
# IMGREG3 - 40%  IMGREG4 - 20%

PROPERTY_MIRROR_FLIP = "MIRLRE"
# MIRLRE1 - ON  MIRLRE0 - OFF (default)

PROPERTY_USB_DATA_FORMAT = "UTFEAN"
PROPERTY_SERIAL_DATA_FORMAT = "232UTF"
PROPERTY_INVOICE_MODE = "SPCINV"
PROPERTY_VIRTUAL_KEYBOARD = "KBDVIR"

PROPERTY_COMM_MODE = "POR"
# PORKBD - USB-KBW  PORHID - USB-HID  PORVIC - USB-COM  POR232 - TTL/RS232

PROPERTY_BAUD_RATE = "232BAD"
# 232BAD2=1200  232BAD3=2400  232BAD4=4800  232BAD5=9600
# 232BAD6=19200  232BAD7=38400  232BAD8=57600  232BAD9=115200 (default)

PROPERTY_READING_MODE = "SCM"
# SCMMAN - Manual (default)  SCMCNT - Continuous  SCMMDH - Motion

PROPERTY_CONTINUOUS_MODE_INTERVAL = "CNTALW"
# CNTALW0 - Once  CNTALW1 - No interval
# CNTALW2 - 0.5 s interval  CNTALW3 - 1 s interval

PROPERTY_MOTION_SENSITIVITY = "MDTTHR"
# MDTTHR15 - Highest  MDTTHR20 - High (default)
# MDTTHR30  MDTTHR50  MDTTHR100 - Lowest

PROPERTY_TRANSFER_CODE_ID = "CIDENA"
PROPERTY_KBD_CASE_CONVERSION = "KBDCNV"

PROPERTY_ENABLE_ALL_1D = "ODCENA"
PROPERTY_DISABLE_ALL_1D = "ODCDIS"
PROPERTY_ENABLE_ALL_2D = "AQRENA"
PROPERTY_DISABLE_ALL_2D = "AQRDIS"

_BAUD_MAP = {
    1200: "2",
    2400: "3",
    4800: "4",
    9600: "5",
    19200: "6",
    38400: "7",
    57600: "8",
    115200: "9",
}
_AREA_MAP = {100: "0", 80: "1", 60: "2", 40: "3", 20: "4"}
_MOTION_VALID = frozenset({15, 20, 30, 50, 100})
_MAX_BARCODE_LEN = 256


class DE2120:
    """Driver for the DE2120 2D barcode scanner engine over UART."""

    def __init__(self, uart=None, tx=None, rx=None, uart_id=1):
        """
        Initialize with either a pre-built UART object or tx/rx pin numbers.
        If tx/rx are given, a UART(uart_id) is created internally at 9600 baud.
        """
        if uart is not None:
            self._uart = uart
        elif tx is not None and rx is not None:
            self._uart = UART(uart_id, baudrate=9600, tx=tx, rx=rx)
        else:
            raise ValueError("Provide a UART object or tx and rx pin numbers")
        self._rx_buf = bytearray()

    def begin(self):
        """Verify communication with the scanner. Returns True on success."""
        if not self._isConnected():
            return False
        while self._uart.any():
            self._uart.read(1)
        return True

    def _isConnected(self):
        self._uart.init(baudrate=9600)
        if self._sendCommand(COMMAND_GET_VERSION, "", 800):
            return True

        self._uart.init(baudrate=115200)
        time.sleep_ms(10)
        self._sendCommand(PROPERTY_BAUD_RATE, "5", 500)

        self._uart.init(baudrate=9600)
        time.sleep_ms(10)
        return self._sendCommand(COMMAND_GET_VERSION, "", 800)

    def factoryDefault(self):
        """Reset scanner to all factory default settings."""
        return self._sendCommand(COMMAND_SET_DEFAULTS)

    def available(self):
        """Return True if bytes are waiting in the UART receive buffer."""
        return self._uart.any() > 0

    def read(self):
        """Read one raw byte from the UART buffer, or -1 if none available."""
        b = self._uart.read(1)
        return b[0] if b else -1

    def _sendCommand(self, cmd, arg="", max_wait_ms=3000):
        self._uart.write(("^_^" + cmd + arg + ".").encode())
        deadline = time.ticks_add(time.ticks_ms(), max_wait_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            while self._uart.any():
                b = self._uart.read(1)
                if b:
                    if b[0] == DE2120_COMMAND_ACK:
                        return True
                    if b[0] == DE2120_COMMAND_NACK:
                        return False
            time.sleep_ms(1)
        return False

    def sendCommand(self, cmd, arg="", max_wait_ms=3000):
        """Send an arbitrary command string to the scanner. Returns True on ACK."""
        return self._sendCommand(cmd, arg, max_wait_ms)

    def readBarcode(self):
        """
        Read a barcode from the scanner. Call repeatedly in a loop.
        Returns the barcode string when a complete CR-terminated scan arrives,
        or None if no complete scan is available yet.
        """
        if not self._uart.any() and not self._rx_buf:
            return None
        while self._uart.any():
            b = self._uart.read(1)
            if not b:
                break
            byte = b[0]
            if byte == 0x0D:  # carriage return marks end of scan
                result = "".join(chr(b) for b in self._rx_buf)
                self._rx_buf = bytearray()
                return result
            if len(self._rx_buf) < _MAX_BARCODE_LEN:
                self._rx_buf.append(byte)
        return None

    def changeBaudRate(self, baud):
        """Change module baud rate. Valid values: 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200."""
        arg = _BAUD_MAP.get(baud)
        return self._sendCommand(PROPERTY_BAUD_RATE, arg) if arg else False

    def changeBuzzerTone(self, tone):
        """Set buzzer frequency: 1=low, 2=medium, 3=high."""
        if 1 <= tone <= 3:
            return self._sendCommand(PROPERTY_BUZZER_FREQ, str(tone))
        return False

    def enableDecodeBeep(self):
        return self._sendCommand(PROPERTY_DECODE_BEEP, "1")

    def disableDecodeBeep(self):
        return self._sendCommand(PROPERTY_DECODE_BEEP, "0")

    def enableBootBeep(self):
        return self._sendCommand(PROPERTY_BOOT_BEEP, "1")

    def disableBootBeep(self):
        return self._sendCommand(PROPERTY_BOOT_BEEP, "0")

    def lightOn(self):
        """Enable the white illumination LED."""
        return self._sendCommand(PROPERTY_FLASH_LIGHT, "1")

    def lightOff(self):
        return self._sendCommand(PROPERTY_FLASH_LIGHT, "0")

    def reticleOn(self):
        """Enable the red aim/reticle laser."""
        return self._sendCommand(PROPERTY_AIM_LIGHT, "1")

    def reticleOff(self):
        return self._sendCommand(PROPERTY_AIM_LIGHT, "0")

    def changeReadingArea(self, percent):
        """Set scanning area as a percentage of the frame: 100, 80, 60, 40, or 20."""
        arg = _AREA_MAP.get(percent)
        return (
            self._sendCommand(PROPERTY_READING_AREA, arg) if arg is not None else False
        )

    def enableImageFlipping(self):
        return self._sendCommand(PROPERTY_MIRROR_FLIP, "1")

    def disableImageFlipping(self):
        return self._sendCommand(PROPERTY_MIRROR_FLIP, "0")

    def enableContinuousRead(self, repeat_interval=2):
        """
        Enable continuous read mode.
        repeat_interval: 0=output once, 1=no delay, 2=0.5 s delay, 3=1 s delay.
        """
        if 0 <= repeat_interval <= 3:
            self._sendCommand(PROPERTY_READING_MODE, "CNT")
            return self._sendCommand(
                PROPERTY_CONTINUOUS_MODE_INTERVAL, str(repeat_interval)
            )
        return False

    def disableContinuousRead(self):
        return self._sendCommand(PROPERTY_READING_MODE, "MAN")

    def enableMotionSense(self, sensitivity=50):
        """
        Enable motion-triggered scanning.
        sensitivity: 15=highest, 20=high (default), 30, 50, 100=lowest.
        """
        if sensitivity in _MOTION_VALID:
            self._sendCommand(PROPERTY_READING_MODE, "MDH")
            return self._sendCommand(PROPERTY_MOTION_SENSITIVITY, str(sensitivity))
        return False

    def disableMotionSense(self):
        return self._sendCommand(PROPERTY_READING_MODE, "MAN")

    def enableAll1D(self):
        return self._sendCommand(PROPERTY_ENABLE_ALL_1D)

    def disableAll1D(self):
        return self._sendCommand(PROPERTY_DISABLE_ALL_1D)

    def enableAll2D(self):
        return self._sendCommand(PROPERTY_ENABLE_ALL_2D)

    def disableAll2D(self):
        return self._sendCommand(PROPERTY_DISABLE_ALL_2D)

    def startScan(self):
        """Trigger a single scan in manual (trigger) mode."""
        return self._sendCommand(COMMAND_START_SCAN)

    def stopScan(self):
        """Stop an in-progress scan."""
        return self._sendCommand(COMMAND_STOP_SCAN)
