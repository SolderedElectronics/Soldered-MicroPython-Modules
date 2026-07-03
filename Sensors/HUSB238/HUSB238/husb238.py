# FILE: husb238.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the HUSB238 USB-PD sink breakout
# LAST UPDATED: 2026-07-03

from machine import I2C, Pin
from os import uname
import time

# Default (fixed) I2C address of the HUSB238
HUSB238_ADDRESS = 0x08

# Register map
HUSB238_REG_PD_STATUS0  = 0x00
HUSB238_REG_PD_STATUS1  = 0x01
HUSB238_REG_SRC_PDO_5V  = 0x02
HUSB238_REG_SRC_PDO_9V  = 0x03
HUSB238_REG_SRC_PDO_12V = 0x04
HUSB238_REG_SRC_PDO_15V = 0x05
HUSB238_REG_SRC_PDO_18V = 0x06
HUSB238_REG_SRC_PDO_20V = 0x07
HUSB238_REG_SRC_PDO     = 0x08
HUSB238_REG_GO_COMMAND  = 0x09

# GO_COMMAND values
HUSB238_CMD_REQUEST_PDO = 0x01
HUSB238_CMD_HARD_RESET  = 0x10

###########################
# Voltage codes           #
# (status read side, PD_STATUS0[7:4], sequential)
###########################
HUSB238_VOLTAGE_UNATTACHED = 0
HUSB238_VOLTAGE_5V         = 1
HUSB238_VOLTAGE_9V         = 2
HUSB238_VOLTAGE_12V        = 3
HUSB238_VOLTAGE_15V        = 4
HUSB238_VOLTAGE_18V        = 5
HUSB238_VOLTAGE_20V        = 6

###########################
# PD select codes         #
# (request side, SRC_PDO[7:4], NOT sequential on this chip)
###########################
HUSB238_PD_SEL_NONE = 0b0000
HUSB238_PD_SEL_5V   = 0b0001
HUSB238_PD_SEL_9V   = 0b0010
HUSB238_PD_SEL_12V  = 0b0011
HUSB238_PD_SEL_15V  = 0b1000
HUSB238_PD_SEL_18V  = 0b1001
HUSB238_PD_SEL_20V  = 0b1010

###########################
# PD response codes       #
# (PD_STATUS1[5:3], chip's response to last GO_COMMAND request)
###########################
HUSB238_RESPONSE_NONE              = 0b000
HUSB238_RESPONSE_SUCCESS           = 0b001
HUSB238_RESPONSE_INVALID_CMD       = 0b011
HUSB238_RESPONSE_NOT_SUPPORTED     = 0b100
HUSB238_RESPONSE_TRANSACTION_FAIL  = 0b101

###########################
# requestPD() outcomes    #
###########################
HUSB238_REQUEST_OK                  = "OK"                   # source switched voltage successfully
HUSB238_REQUEST_UNSUPPORTED_VOLTAGE = "UNSUPPORTED_VOLTAGE"   # voltage not one of 5/9/12/15/18/20
HUSB238_REQUEST_NOT_OFFERED         = "NOT_OFFERED"           # source does not advertise this voltage
HUSB238_REQUEST_REJECTED            = "REJECTED"              # source rejected the request


class HUSB238:
    """
    MicroPython class for the HUSB238 USB-PD sink breakout.
    Communicates over I2C, fixed address 0x08.
    """

    def __init__(self, i2c=None, address=HUSB238_ADDRESS):
        """
        Initialize the HUSB238.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address of the device (fixed to 0x08 on this breakout)
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.address = address

    def begin(self):
        """
        Verify communication with the HUSB238.

        :return: bool, True if device is reachable, False otherwise
        """
        try:
            self._readRegister(HUSB238_REG_PD_STATUS0)
            return True
        except OSError:
            return False

    def isAttached(self):
        """
        Check if a PD source is attached.

        :return: bool, True if attached
        """
        status1 = self._readRegister(HUSB238_REG_PD_STATUS1)
        return (status1 & 0x40) != 0

    def isVoltageDetected(self, voltage):
        """
        Check if the source offers a specific voltage.

        :param voltage: float, voltage to check for, one of 5, 9, 12, 15, 18, 20
        :return: bool, True if that voltage is offered by the source
        """
        reg = self._voltagePDORegister(voltage)
        if reg == 0:
            return False

        value = self._readRegister(reg)
        return (value & 0x80) != 0

    def getPDSrcVoltage(self):
        """
        Read currently negotiated source voltage.

        :return: float, voltage in volts, 0 if unattached
        """
        status0 = self._readRegister(HUSB238_REG_PD_STATUS0)
        code = (status0 >> 4) & 0x0F
        return self._voltageCodeToFloat(code)

    def getPDSrcCurrent(self):
        """
        Read currently negotiated source max current.

        :return: float, current in amps
        """
        status0 = self._readRegister(HUSB238_REG_PD_STATUS0)
        code = status0 & 0x0F
        return self._currentCodeToFloat(code)

    def getPDResponse(self):
        """
        Read the source's response to the last request.

        :return: int, HUSB238_RESPONSE_* code from PD_STATUS1[5:3]
        """
        status1 = self._readRegister(HUSB238_REG_PD_STATUS1)
        return (status1 >> 3) & 0x07

    def requestPD(self, voltage):
        """
        Request the source to switch to a given voltage.
        Blocks briefly to read back the source's response.

        :param voltage: float, voltage to request, one of 5, 9, 12, 15, 18, 20
        :return: str, HUSB238_REQUEST_* outcome constant
        """
        code = self._voltageToSelectCode(voltage)
        if code == HUSB238_PD_SEL_NONE:
            return HUSB238_REQUEST_UNSUPPORTED_VOLTAGE

        if not self.isVoltageDetected(voltage):
            return HUSB238_REQUEST_NOT_OFFERED

        self._writeRegister(HUSB238_REG_SRC_PDO, code << 4)
        self._writeRegister(HUSB238_REG_GO_COMMAND, HUSB238_CMD_REQUEST_PDO)

        time.sleep_ms(300)

        if self.getPDResponse() != HUSB238_RESPONSE_SUCCESS:
            return HUSB238_REQUEST_REJECTED

        return HUSB238_REQUEST_OK

    def reset(self):
        """
        Send a hard reset command to the chip.
        """
        self._writeRegister(HUSB238_REG_GO_COMMAND, HUSB238_CMD_HARD_RESET)

    def readRawRegister(self, reg):
        """
        Debug helper, reads raw register byte.

        :param reg: int, register address, use HUSB238_REG_* constants
        :return: int, raw register value
        """
        return self._readRegister(reg)

    # -------------------------------------------------------------------------
    # Private: lookup tables
    # -------------------------------------------------------------------------

    def _voltagePDORegister(self, voltage):
        if voltage == 5:
            return HUSB238_REG_SRC_PDO_5V
        if voltage == 9:
            return HUSB238_REG_SRC_PDO_9V
        if voltage == 12:
            return HUSB238_REG_SRC_PDO_12V
        if voltage == 15:
            return HUSB238_REG_SRC_PDO_15V
        if voltage == 18:
            return HUSB238_REG_SRC_PDO_18V
        if voltage == 20:
            return HUSB238_REG_SRC_PDO_20V

        return 0

    def _voltageToSelectCode(self, voltage):
        if voltage == 5:
            return HUSB238_PD_SEL_5V
        if voltage == 9:
            return HUSB238_PD_SEL_9V
        if voltage == 12:
            return HUSB238_PD_SEL_12V
        if voltage == 15:
            return HUSB238_PD_SEL_15V
        if voltage == 18:
            return HUSB238_PD_SEL_18V
        if voltage == 20:
            return HUSB238_PD_SEL_20V

        return HUSB238_PD_SEL_NONE

    def _voltageCodeToFloat(self, code):
        if code == HUSB238_VOLTAGE_5V:
            return 5
        if code == HUSB238_VOLTAGE_9V:
            return 9
        if code == HUSB238_VOLTAGE_12V:
            return 12
        if code == HUSB238_VOLTAGE_15V:
            return 15
        if code == HUSB238_VOLTAGE_18V:
            return 18
        if code == HUSB238_VOLTAGE_20V:
            return 20

        return 0

    def _currentCodeToFloat(self, code):
        table = {
            0b0000: 0.5,
            0b0001: 0.7,
            0b0010: 1.0,
            0b0011: 1.25,
            0b0100: 1.5,
            0b0101: 1.75,
            0b0110: 2.0,
            0b0111: 2.25,
            0b1000: 2.5,
            0b1001: 2.75,
            0b1010: 3.0,
            0b1011: 3.25,
            0b1100: 3.5,
            0b1101: 4.0,
            0b1110: 4.5,
            0b1111: 5.0,
        }
        return table.get(code, 0)

    # -------------------------------------------------------------------------
    # Private: I2C register access
    # -------------------------------------------------------------------------

    def _readRegister(self, reg):
        try:
            return self.i2c.readfrom_mem(self.address, reg, 1)[0]
        except OSError:
            return 0

    def _writeRegister(self, reg, value):
        self.i2c.writeto_mem(self.address, reg, bytes([value]))
