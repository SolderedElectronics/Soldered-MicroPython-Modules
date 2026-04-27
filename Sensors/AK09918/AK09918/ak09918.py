# FILE: ak09918.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython library for the AK09918 3-axis digital compass sensor
# LAST UPDATED: 2026-04-23

import time
from machine import I2C, Pin
from os import uname
from ak09918_constants import (
    AK09918_I2C_ADDR,
    AK09918_WIA1,
    AK09918_ST1,
    AK09918_HXL,
    AK09918_CNTL2,
    AK09918_CNTL3,
    AK09918_DRDY_BIT,
    AK09918_DOR_BIT,
    AK09918_HOFL_BIT,
    AK09918_SRST_BIT,
    AK09918_ERR_OK,
    AK09918_ERR_DOR,
    AK09918_ERR_NOT_RDY,
    AK09918_ERR_TIMEOUT,
    AK09918_ERR_SELFTEST_FAILED,
    AK09918_ERR_OVERFLOW,
    AK09918_ERR_WRITE_FAILED,
    AK09918_ERR_READ_FAILED,
    AK09918_POWER_DOWN,
    AK09918_NORMAL,
    AK09918_SELF_TEST,
)


class AK09918:
    """
    MicroPython class for the AK09918 3-axis digital compass sensor.
    Supports single-measurement, continuous, and self-test modes.
    """

    def __init__(self, i2c=None, address=AK09918_I2C_ADDR, mode=AK09918_POWER_DOWN):
        """
        Initialize the AK09918 sensor.

        :param i2c: Initialized I2C object
        :param address: I2C address of the sensor (default 0x0C)
        :param mode: Initial operating mode (default AK09918_POWER_DOWN)
        """
        if i2c != None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.address = address
        self._mode = AK09918_POWER_DOWN

        if mode == AK09918_SELF_TEST:
            mode = AK09918_POWER_DOWN

        if mode != AK09918_POWER_DOWN:
            self.switchMode(mode)

    # Read a single byte from a register, returns (success, value)
    def _readByte(self, reg):
        try:
            data = self.i2c.readfrom_mem(self.address, reg, 1)
            return True, data[0]
        except:
            return False, 0

    # Read multiple bytes starting from a register, returns (success, bytes)
    def _readBytes(self, reg, count):
        try:
            data = self.i2c.readfrom_mem(self.address, reg, count)
            return True, data
        except:
            return False, bytes(count)

    # Write a single byte to a register, returns success bool
    def _writeByte(self, reg, val):
        try:
            self.i2c.writeto_mem(self.address, reg, bytes([val]))
            return True
        except:
            return False

    # Read the current raw mode value from CNTL2
    def _getRawMode(self):
        ok, val = self._readByte(AK09918_CNTL2)
        if not ok:
            return 0xFF
        return val

    def isDataReady(self):
        """
        Check whether new measurement data is available.

        :return: AK09918_ERR_OK if data is ready, AK09918_ERR_NOT_RDY if not,
                 or AK09918_ERR_READ_FAILED on a bus error
        """
        ok, val = self._readByte(AK09918_ST1)
        if not ok:
            return AK09918_ERR_READ_FAILED
        return AK09918_ERR_OK if (val & AK09918_DRDY_BIT) else AK09918_ERR_NOT_RDY

    def isDataSkip(self):
        """
        Check whether any measurement was overwritten before being read.

        :return: AK09918_ERR_DOR if data was skipped, AK09918_ERR_OK if not,
                 or AK09918_ERR_READ_FAILED on a bus error
        """
        ok, val = self._readByte(AK09918_ST1)
        if not ok:
            return AK09918_ERR_READ_FAILED
        return AK09918_ERR_DOR if (val & AK09918_DOR_BIT) else AK09918_ERR_OK

    def getRawData(self):
        """
        Read raw ADC values directly from the output registers.

        For AK09918_NORMAL mode, triggers a single measurement and blocks until complete.
        For continuous modes, reads the latest available sample immediately.

        :return: (err, x, y, z) raw ADC counts as signed integers
        """
        if self._mode == AK09918_NORMAL:
            self.switchMode(AK09918_NORMAL)
            retries = 0
            while self._getRawMode() != 0x00:
                if retries >= 15:
                    return AK09918_ERR_TIMEOUT, 0, 0, 0
                retries += 1
                time.sleep_ms(1)

        ok, buf = self._readBytes(AK09918_HXL, 8)
        if not ok:
            return AK09918_ERR_READ_FAILED, 0, 0, 0

        x = (buf[1] << 8) | buf[0]
        y = (buf[3] << 8) | buf[2]
        z = (buf[5] << 8) | buf[4]

        # Convert to signed 16-bit
        if x > 32767:
            x -= 65536
        if y > 32767:
            y -= 65536
        if z > 32767:
            z -= 65536

        if buf[7] & AK09918_HOFL_BIT:
            return AK09918_ERR_OVERFLOW, x, y, z

        return AK09918_ERR_OK, x, y, z

    def getData(self):
        """
        Read calibrated magnetic field values.

        Each raw ADC count is multiplied by 0.15 (sensor sensitivity in µT/LSB).
        The result is an integer where 1 unit ≈ 0.15 µT.

        For AK09918_NORMAL mode, triggers a fresh single measurement.
        For continuous modes, reads the latest available sample.

        :return: (err, x, y, z) calibrated values
        """
        err, x, y, z = self.getRawData()
        x = x * 15 // 100
        y = y * 15 // 100
        z = z * 15 // 100
        return err, x, y, z

    def getMode(self):
        """
        Return the currently active operating mode.

        :return: The mode constant last written to CNTL2
        """
        return self._mode

    def switchMode(self, mode):
        """
        Change the sensor operating mode.

        AK09918_SELF_TEST cannot be set through this function; use selfTest() instead.

        :param mode: New mode to apply
        :return: AK09918_ERR_OK on success, AK09918_ERR_WRITE_FAILED on failure
        """
        if mode == AK09918_SELF_TEST:
            return AK09918_ERR_WRITE_FAILED
        self._mode = mode
        if not self._writeByte(AK09918_CNTL2, mode):
            return AK09918_ERR_WRITE_FAILED
        return AK09918_ERR_OK

    def selfTest(self):
        """
        Execute the built-in hardware self-test.

        Powers the sensor down, triggers the self-test sequence, and verifies that
        the output falls within datasheet limits (X/Y: ±200 counts, Z: −1000 to −150).

        :return: AK09918_ERR_OK if the test passes, AK09918_ERR_SELFTEST_FAILED if
                 output is out of range, or an I2C error code on communication failure
        """
        if not self._writeByte(AK09918_CNTL2, AK09918_POWER_DOWN):
            return AK09918_ERR_WRITE_FAILED
        time.sleep_ms(1)
        if not self._writeByte(AK09918_CNTL2, AK09918_SELF_TEST):
            return AK09918_ERR_WRITE_FAILED

        while True:
            err = self.isDataReady()
            if err == AK09918_ERR_READ_FAILED:
                return AK09918_ERR_READ_FAILED
            if err == AK09918_ERR_OK:
                break
            time.sleep_ms(1)

        ok, buf = self._readBytes(AK09918_HXL, 8)
        if not ok:
            return AK09918_ERR_READ_FAILED

        x = (buf[1] << 8) | buf[0]
        y = (buf[3] << 8) | buf[2]
        z = (buf[5] << 8) | buf[4]

        if x > 32767:
            x -= 65536
        if y > 32767:
            y -= 65536
        if z > 32767:
            z -= 65536

        if -200 <= x <= 200 and -200 <= y <= 200 and -1000 <= z <= -150:
            return AK09918_ERR_OK
        return AK09918_ERR_SELFTEST_FAILED

    def reset(self):
        """
        Perform a software reset. All registers return to power-on defaults.

        :return: AK09918_ERR_OK on success, AK09918_ERR_WRITE_FAILED on failure
        """
        if not self._writeByte(AK09918_CNTL3, AK09918_SRST_BIT):
            return AK09918_ERR_WRITE_FAILED
        return AK09918_ERR_OK

    def strError(self, err):
        """
        Convert an error code into a human-readable string.

        :param err: Error code to describe
        :return: String describing the error
        """
        errors = {
            AK09918_ERR_OK: "OK",
            AK09918_ERR_DOR: "Data overrun: measurement was overwritten before being read",
            AK09918_ERR_NOT_RDY: "Not ready: measurement still in progress",
            AK09918_ERR_TIMEOUT: "Timeout: sensor did not complete measurement in time",
            AK09918_ERR_SELFTEST_FAILED: "Self-test failed: output out of specified range",
            AK09918_ERR_OVERFLOW: "Overflow: magnetic field exceeded measurable range",
            AK09918_ERR_WRITE_FAILED: "Write failed: I2C write error",
            AK09918_ERR_READ_FAILED: "Read failed: I2C read error",
        }
        return errors.get(err, "Unknown error")

    def getDeviceID(self):
        """
        Read the device identification registers.

        WIA1 contains the company ID (0x48) and WIA2 contains the device ID (0x0A).
        The expected combined value is 0x480A.

        :return: 16-bit value with WIA1 in the high byte and WIA2 in the low byte
        """
        ok, buf = self._readBytes(AK09918_WIA1, 2)
        if not ok:
            return 0
        return (buf[0] << 8) | buf[1]
