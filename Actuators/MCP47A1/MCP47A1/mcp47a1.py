# FILE: mcp47a1.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the MCP47A1 DAC
# LAST UPDATED: 2026-04-29

from machine import I2C, Pin
from os import uname

MCP47A1_I2C_ADDR = 0x2E

class MCP47A1:
    """
    MicroPython class for the MCP47A1 DAC.
    """

    dacSupply = 3.3

    def __init__(self, i2c=None, address=MCP47A1_I2C_ADDR):
        """
        Initialize the MCP47A1 DAC.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address of the device (default 0x5C)
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")
        
        self.address = address


    def writeByte(self, val):
      """
      Set voltage at with digital word (byte).

      :param val: DAC digital word (byte) in range from 0 to 64
      """
      try:
          buf = bytes([0x00, int(val)])
          self.i2c.writeto(self.address, buf)
          return True
      except Exception as e:
          print("Write error:", e)
          return False


    def readByte(self):
        """
        Get digital word from DAC (byte) that represents output voltage.

        :return: Digital word in range from 0 (0V) to 64 (VCC)
        """
        try:
            self.i2c.writeto(self.address, bytes([0x00]))
            data = self.i2c.readfrom(self.address, 1)
            return True, data[0]
        except Exception as e:
            print("Read error:", e)
            return False, 0

    def setVoltage(self, voltage):
        """
        Set DAC output voltage.

        :param voltage: Voltage at DACs output in range from 0V to VCC
        """
        if voltage < 0 or voltage > self.dacSupply:
            return False

        byte = int(voltage / self.dacSupply * 64)
        return self._writeByte(byte)

    def dacVcc(self, vcc):
        """
        Set supply voltage of DAC (needed for calculation).
        
        Use if only if you are VCC pin instead of easyC connector. 
        Default value is 3.3V (easyC * voltage).

        :param vcc: Supply voltage of DAC (in range from 1.8V to 5.5V)
        """
        if (vcc > 5 or vcc < 1.8):
            return
        self.dacSupply = vcc

    def getVoltage(self):
        """
        Get currently set voltage at the DACs output.

        :return: Voltage at DAC output
        """
        success, byte = self._readByte()
        if not success:
            return None
        return byte / 64 * self.dacSupply