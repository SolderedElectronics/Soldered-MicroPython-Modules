# FILE: bq27441.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the BQ27441-G1A LiPo Fuel Gauge
# LAST UPDATED: 2026-05-06

from machine import I2C, Pin
from os import uname
import time

# Default I2C address
BQ27441_I2C_ADDRESS = 0x55

# Device ID
BQ27441_DEVICE_ID = 0x0421

# Unseal key
BQ27441_UNSEAL_KEY = 0x8000

# I2C timeout (ms)
BQ27441_I2C_TIMEOUT = 2000

###########################
# Standard Commands       #
###########################
BQ27441_COMMAND_CONTROL         = 0x00
BQ27441_COMMAND_TEMP            = 0x02
BQ27441_COMMAND_VOLTAGE         = 0x04
BQ27441_COMMAND_FLAGS           = 0x06
BQ27441_COMMAND_NOM_CAPACITY    = 0x08
BQ27441_COMMAND_AVAIL_CAPACITY  = 0x0A
BQ27441_COMMAND_REM_CAPACITY    = 0x0C
BQ27441_COMMAND_FULL_CAPACITY   = 0x0E
BQ27441_COMMAND_AVG_CURRENT     = 0x10
BQ27441_COMMAND_STDBY_CURRENT   = 0x12
BQ27441_COMMAND_MAX_CURRENT     = 0x14
BQ27441_COMMAND_AVG_POWER       = 0x18
BQ27441_COMMAND_SOC             = 0x1C
BQ27441_COMMAND_INT_TEMP        = 0x1E
BQ27441_COMMAND_SOH             = 0x20
BQ27441_COMMAND_REM_CAP_UNFL    = 0x28
BQ27441_COMMAND_REM_CAP_FIL     = 0x2A
BQ27441_COMMAND_FULL_CAP_UNFL   = 0x2C
BQ27441_COMMAND_FULL_CAP_FIL    = 0x2E
BQ27441_COMMAND_SOC_UNFL        = 0x30

###########################
# Control Sub-commands    #
###########################
BQ27441_CONTROL_STATUS          = 0x00
BQ27441_CONTROL_DEVICE_TYPE     = 0x01
BQ27441_CONTROL_FW_VERSION      = 0x02
BQ27441_CONTROL_DM_CODE         = 0x04
BQ27441_CONTROL_PREV_MACWRITE   = 0x07
BQ27441_CONTROL_CHEM_ID         = 0x08
BQ27441_CONTROL_BAT_INSERT      = 0x0C
BQ27441_CONTROL_BAT_REMOVE      = 0x0D
BQ27441_CONTROL_SET_HIBERNATE   = 0x11
BQ27441_CONTROL_CLEAR_HIBERNATE = 0x12
BQ27441_CONTROL_SET_CFGUPDATE   = 0x13
BQ27441_CONTROL_SHUTDOWN_ENABLE = 0x1B
BQ27441_CONTROL_SHUTDOWN        = 0x1C
BQ27441_CONTROL_SEALED          = 0x20
BQ27441_CONTROL_PULSE_SOC_INT   = 0x23
BQ27441_CONTROL_RESET           = 0x41
BQ27441_CONTROL_SOFT_RESET      = 0x42
BQ27441_CONTROL_EXIT_CFGUPDATE  = 0x43
BQ27441_CONTROL_EXIT_RESIM      = 0x44

###########################
# Control Status Bits     #
###########################
BQ27441_STATUS_SHUTDOWNEN = (1 << 15)
BQ27441_STATUS_WDRESET    = (1 << 14)
BQ27441_STATUS_SS         = (1 << 13)
BQ27441_STATUS_CALMODE    = (1 << 12)
BQ27441_STATUS_CCA        = (1 << 11)
BQ27441_STATUS_BCA        = (1 << 10)
BQ27441_STATUS_QMAX_UP    = (1 << 9)
BQ27441_STATUS_RES_UP     = (1 << 8)
BQ27441_STATUS_INITCOMP   = (1 << 7)
BQ27441_STATUS_HIBERNATE  = (1 << 6)
BQ27441_STATUS_SLEEP      = (1 << 4)
BQ27441_STATUS_LDMD       = (1 << 3)
BQ27441_STATUS_RUP_DIS    = (1 << 2)
BQ27441_STATUS_VOK        = (1 << 1)

###########################
# Flags Bits              #
###########################
BQ27441_FLAG_OT         = (1 << 15)
BQ27441_FLAG_UT         = (1 << 14)
BQ27441_FLAG_FC         = (1 << 9)
BQ27441_FLAG_CHG        = (1 << 8)
BQ27441_FLAG_OCVTAKEN   = (1 << 7)
BQ27441_FLAG_ITPOR      = (1 << 5)
BQ27441_FLAG_CFGUPMODE  = (1 << 4)
BQ27441_FLAG_BAT_DET    = (1 << 3)
BQ27441_FLAG_SOC1       = (1 << 2)
BQ27441_FLAG_SOCF       = (1 << 1)
BQ27441_FLAG_DSG        = (1 << 0)

###########################
# Extended Data Commands  #
###########################
BQ27441_EXTENDED_OPCONFIG  = 0x3A
BQ27441_EXTENDED_CAPACITY  = 0x3C
BQ27441_EXTENDED_DATACLASS = 0x3E
BQ27441_EXTENDED_DATABLOCK = 0x3F
BQ27441_EXTENDED_BLOCKDATA = 0x40
BQ27441_EXTENDED_CHECKSUM  = 0x60
BQ27441_EXTENDED_CONTROL   = 0x61

###########################
# Configuration Class IDs #
###########################
BQ27441_ID_SAFETY          = 2
BQ27441_ID_CHG_TERMINATION = 36
BQ27441_ID_CONFIG_DATA     = 48
BQ27441_ID_DISCHARGE       = 49
BQ27441_ID_REGISTERS       = 64
BQ27441_ID_POWER           = 68
BQ27441_ID_IT_CFG          = 80
BQ27441_ID_CURRENT_THRESH  = 81
BQ27441_ID_STATE           = 82
BQ27441_ID_R_A_RAM         = 89
BQ27441_ID_CALIB_DATA      = 104
BQ27441_ID_CC_CAL          = 105
BQ27441_ID_CURRENT         = 107
BQ27441_ID_CODES           = 112

###########################
# OpConfig Bits           #
###########################
BQ27441_OPCONFIG_BIE      = (1 << 13)
BQ27441_OPCONFIG_BI_PU_EN = (1 << 12)
BQ27441_OPCONFIG_GPIOPOL  = (1 << 11)
BQ27441_OPCONFIG_SLEEP    = (1 << 5)
BQ27441_OPCONFIG_RMFCC    = (1 << 4)
BQ27441_OPCONFIG_BATLOWEN = (1 << 2)
BQ27441_OPCONFIG_TEMPS    = (1 << 0)

# current() type constants
AVG  = 0  # Average Current (default)
STBY = 1  # Standby Current
MAX  = 2  # Max Current

# capacity() type constants
REMAIN     = 0  # Remaining Capacity (default)
FULL       = 1  # Full Capacity
AVAIL      = 2  # Available Capacity
AVAIL_FULL = 3  # Full Available Capacity
REMAIN_F   = 4  # Remaining Capacity Filtered
REMAIN_UF  = 5  # Remaining Capacity Unfiltered
FULL_F     = 6  # Full Capacity Filtered
FULL_UF    = 7  # Full Capacity Unfiltered
DESIGN     = 8  # Design Capacity

# soc() type constants
FILTERED   = 0  # State of Charge Filtered (default)
UNFILTERED = 1  # State of Charge Unfiltered

# soh() type constants
PERCENT  = 0  # State of Health Percentage (default)
SOH_STAT = 1  # State of Health Status Bits

# temperature() type constants
BATTERY       = 0  # Battery Temperature (default)
INTERNAL_TEMP = 1  # Internal IC Temperature

# setGPOUTFunction() type constants
SOC_INT = 0  # GPOUT set to SOC_INT functionality
BAT_LOW = 1  # GPOUT set to BAT_LOW functionality


class BQ27441:
    """
    MicroPython class for the BQ27441-G1A LiPo Fuel Gauge.
    Communicates over I2C to read battery voltage, current, capacity,
    state of charge, state of health, and temperature.
    """

    def __init__(self, i2c=None, address=BQ27441_I2C_ADDRESS):
        """
        Initialize the BQ27441 fuel gauge.

        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param address: I2C address of the device (default 0x55)
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
        self._seal_flag = False          # Track if IC was sealed before config entry
        self._user_config_control = False  # Track if user is managing config mode

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def begin(self):
        """
        Verify communication with the BQ27441. Must be called before any other method.

        :return: True if device ID matches, False otherwise
        """
        return self.deviceType() == BQ27441_DEVICE_ID

    def setCapacity(self, capacity):
        """
        Configure the design capacity of the connected battery.

        :param capacity: Battery capacity in mAh (uint16)
        :return: True on success
        """
        data = bytes([capacity >> 8, capacity & 0xFF])
        return self._writeExtendedData(BQ27441_ID_STATE, 10, data)

    def setDesignEnergy(self, energy):
        """
        Configure the design energy of the connected battery.

        :param energy: Battery energy in mWh (uint16)
        :return: True on success
        """
        data = bytes([energy >> 8, energy & 0xFF])
        return self._writeExtendedData(BQ27441_ID_STATE, 12, data)

    def setTerminateVoltage(self, voltage):
        """
        Configure the terminate voltage (lowest operational battery voltage).

        :param voltage: Voltage in mV, clamped to 2500-3700
        :return: True on success
        """
        voltage = max(2500, min(3700, voltage))
        data = bytes([voltage >> 8, voltage & 0xFF])
        return self._writeExtendedData(BQ27441_ID_STATE, 16, data)

    def setTaperRate(self, rate):
        """
        Configure the taper rate of the connected battery.

        :param rate: Taper rate in units of 0.1h, max 2000
        :return: True on success
        """
        rate = min(2000, rate)
        data = bytes([rate >> 8, rate & 0xFF])
        return self._writeExtendedData(BQ27441_ID_STATE, 27, data)

    # -------------------------------------------------------------------------
    # Battery Characteristics
    # -------------------------------------------------------------------------

    def voltage(self):
        """
        Read the battery voltage.

        :return: Voltage in mV
        """
        return self._readWord(BQ27441_COMMAND_VOLTAGE)

    def current(self, measure=AVG):
        """
        Read the specified current measurement.

        :param measure: AVG, STBY, or MAX (default AVG)
        :return: Current in mA, positive = charging
        """
        if measure == AVG:
            raw = self._readWord(BQ27441_COMMAND_AVG_CURRENT)
        elif measure == STBY:
            raw = self._readWord(BQ27441_COMMAND_STDBY_CURRENT)
        elif measure == MAX:
            raw = self._readWord(BQ27441_COMMAND_MAX_CURRENT)
        else:
            return 0
        # Convert unsigned 16-bit to signed
        return raw if raw < 0x8000 else raw - 0x10000

    def capacity(self, measure=REMAIN):
        """
        Read the specified capacity measurement.

        :param measure: REMAIN, FULL, AVAIL, AVAIL_FULL, REMAIN_F, REMAIN_UF,
                        FULL_F, FULL_UF, or DESIGN (default REMAIN)
        :return: Capacity in mAh
        """
        if measure == REMAIN:
            return self._readWord(BQ27441_COMMAND_REM_CAPACITY)
        elif measure == FULL:
            return self._readWord(BQ27441_COMMAND_FULL_CAPACITY)
        elif measure == AVAIL:
            return self._readWord(BQ27441_COMMAND_NOM_CAPACITY)
        elif measure == AVAIL_FULL:
            return self._readWord(BQ27441_COMMAND_AVAIL_CAPACITY)
        elif measure == REMAIN_F:
            return self._readWord(BQ27441_COMMAND_REM_CAP_FIL)
        elif measure == REMAIN_UF:
            return self._readWord(BQ27441_COMMAND_REM_CAP_UNFL)
        elif measure == FULL_F:
            return self._readWord(BQ27441_COMMAND_FULL_CAP_FIL)
        elif measure == FULL_UF:
            return self._readWord(BQ27441_COMMAND_FULL_CAP_UNFL)
        elif measure == DESIGN:
            return self._readWord(BQ27441_EXTENDED_CAPACITY)
        return 0

    def power(self):
        """
        Read the average power.

        :return: Power in mW, positive = charging
        """
        raw = self._readWord(BQ27441_COMMAND_AVG_POWER)
        return raw if raw < 0x8000 else raw - 0x10000

    def soc(self, measure=FILTERED):
        """
        Read the state of charge.

        :param measure: FILTERED or UNFILTERED (default FILTERED)
        :return: State of charge in %
        """
        if measure == FILTERED:
            return self._readWord(BQ27441_COMMAND_SOC)
        elif measure == UNFILTERED:
            return self._readWord(BQ27441_COMMAND_SOC_UNFL)
        return 0

    def soh(self, measure=PERCENT):
        """
        Read the state of health.

        :param measure: PERCENT or SOH_STAT (default PERCENT)
        :return: State of health in % or status bits
        """
        raw = self._readWord(BQ27441_COMMAND_SOH)
        soh_status  = (raw >> 8) & 0xFF
        soh_percent = raw & 0xFF
        return soh_percent if measure == PERCENT else soh_status

    def temperature(self, measure=BATTERY):
        """
        Read the specified temperature.

        :param measure: BATTERY or INTERNAL_TEMP (default BATTERY)
        :return: Temperature in units of 0.1 K (divide by 10, subtract 273.15 for °C)
        """
        if measure == BATTERY:
            return self._readWord(BQ27441_COMMAND_TEMP)
        elif measure == INTERNAL_TEMP:
            return self._readWord(BQ27441_COMMAND_INT_TEMP)
        return 0

    # -------------------------------------------------------------------------
    # GPOUT Control
    # -------------------------------------------------------------------------

    def GPOUTPolarity(self):
        """
        Get the GPOUT polarity setting.

        :return: True if active-high, False if active-low
        """
        return bool(self._opConfig() & BQ27441_OPCONFIG_GPIOPOL)

    def setGPOUTPolarity(self, active_high):
        """
        Set GPOUT polarity to active-high or active-low.

        :param active_high: True for active-high, False for active-low
        :return: True on success
        """
        old = self._opConfig()
        if (active_high and (old & BQ27441_OPCONFIG_GPIOPOL)) or \
           (not active_high and not (old & BQ27441_OPCONFIG_GPIOPOL)):
            return True
        new = (old | BQ27441_OPCONFIG_GPIOPOL) if active_high \
              else (old & ~BQ27441_OPCONFIG_GPIOPOL)
        return self._writeOpConfig(new)

    def GPOUTFunction(self):
        """
        Get the GPOUT function setting.

        :return: True if BAT_LOW, False if SOC_INT
        """
        return bool(self._opConfig() & BQ27441_OPCONFIG_BATLOWEN)

    def setGPOUTFunction(self, function):
        """
        Set GPOUT function to BAT_LOW or SOC_INT.

        :param function: BAT_LOW or SOC_INT
        :return: True on success
        """
        old = self._opConfig()
        if (function and (old & BQ27441_OPCONFIG_BATLOWEN)) or \
           (not function and not (old & BQ27441_OPCONFIG_BATLOWEN)):
            return True
        new = (old | BQ27441_OPCONFIG_BATLOWEN) if function \
              else (old & ~BQ27441_OPCONFIG_BATLOWEN)
        return self._writeOpConfig(new)

    def SOC1SetThreshold(self):
        """
        Get the SOC1 set threshold (threshold to set the alert flag).

        :return: State of charge percentage 0-100
        """
        return self._readExtendedData(BQ27441_ID_DISCHARGE, 0)

    def SOC1ClearThreshold(self):
        """
        Get the SOC1 clear threshold (threshold to clear the alert flag).

        :return: State of charge percentage 0-100
        """
        return self._readExtendedData(BQ27441_ID_DISCHARGE, 1)

    def setSOC1Thresholds(self, set_thr, clear_thr):
        """
        Set the SOC1 set and clear thresholds. clear_thr should be > set_thr.

        :param set_thr: Set threshold percentage 0-100
        :param clear_thr: Clear threshold percentage 0-100
        :return: True on success
        """
        data = bytes([max(0, min(100, set_thr)), max(0, min(100, clear_thr))])
        return self._writeExtendedData(BQ27441_ID_DISCHARGE, 0, data)

    def SOCFSetThreshold(self):
        """
        Get the SOCF set threshold (threshold to set the final alert flag).

        :return: State of charge percentage 0-100
        """
        return self._readExtendedData(BQ27441_ID_DISCHARGE, 2)

    def SOCFClearThreshold(self):
        """
        Get the SOCF clear threshold (threshold to clear the final alert flag).

        :return: State of charge percentage 0-100
        """
        return self._readExtendedData(BQ27441_ID_DISCHARGE, 3)

    def setSOCFThresholds(self, set_thr, clear_thr):
        """
        Set the SOCF set and clear thresholds. clear_thr should be > set_thr.

        :param set_thr: Set threshold percentage 0-100
        :param clear_thr: Clear threshold percentage 0-100
        :return: True on success
        """
        data = bytes([max(0, min(100, set_thr)), max(0, min(100, clear_thr))])
        return self._writeExtendedData(BQ27441_ID_DISCHARGE, 2, data)

    def socFlag(self):
        """
        Check if the SOC1 flag is set.

        :return: True if flag is set
        """
        return bool(self.flags() & BQ27441_FLAG_SOC1)

    def socfFlag(self):
        """
        Check if the SOCF flag is set.

        :return: True if flag is set
        """
        return bool(self.flags() & BQ27441_FLAG_SOCF)

    def itporFlag(self):
        """
        Check if the ITPOR flag is set.

        :return: True if flag is set
        """
        return bool(self.flags() & BQ27441_FLAG_ITPOR)

    def fcFlag(self):
        """
        Check if the FC (fully charged) flag is set.

        :return: True if flag is set
        """
        return bool(self.flags() & BQ27441_FLAG_FC)

    def chgFlag(self):
        """
        Check if the CHG (charging) flag is set.

        :return: True if flag is set
        """
        return bool(self.flags() & BQ27441_FLAG_CHG)

    def dsgFlag(self):
        """
        Check if the DSG (discharging) flag is set.

        :return: True if flag is set
        """
        return bool(self.flags() & BQ27441_FLAG_DSG)

    def sociDelta(self):
        """
        Get the SOC_INT interval delta.

        :return: Interval percentage value between 1 and 100
        """
        return self._readExtendedData(BQ27441_ID_STATE, 26)

    def setSOCIDelta(self, delta):
        """
        Set the SOC_INT interval delta.

        :param delta: Percentage interval between 0 and 100
        :return: True on success
        """
        soci = max(0, min(100, delta))
        return self._writeExtendedData(BQ27441_ID_STATE, 26, bytes([soci]))

    def pulseGPOUT(self):
        """
        Pulse the GPOUT pin. Device must be in SOC_INT mode.

        :return: True on success
        """
        return self._executeControlWord(BQ27441_CONTROL_PULSE_SOC_INT)

    # -------------------------------------------------------------------------
    # Control Sub-commands
    # -------------------------------------------------------------------------

    def deviceType(self):
        """
        Read the device type — should return 0x0421.

        :return: 16-bit device type value
        """
        return self._readControlWord(BQ27441_CONTROL_DEVICE_TYPE)

    def enterConfig(self, user_control=True):
        """
        Enter configuration update mode.

        :param user_control: True if the sketch is managing config mode entry/exit
        :return: True on success
        """
        if user_control:
            self._user_config_control = True

        if self._sealed():
            self._seal_flag = True
            self._unseal()

        if self._executeControlWord(BQ27441_CONTROL_SET_CFGUPDATE):
            timeout = BQ27441_I2C_TIMEOUT
            while timeout > 0 and not (self.flags() & BQ27441_FLAG_CFGUPMODE):
                time.sleep_ms(1)
                timeout -= 1
            if timeout > 0:
                return True

        return False

    def exitConfig(self, resim=True):
        """
        Exit configuration update mode.

        :param resim: True to perform OCV resimulation on exit (recommended)
        :return: True on success
        """
        if resim:
            if self._softReset():
                timeout = BQ27441_I2C_TIMEOUT
                while timeout > 0 and (self.flags() & BQ27441_FLAG_CFGUPMODE):
                    time.sleep_ms(1)
                    timeout -= 1
                if timeout > 0:
                    if self._seal_flag:
                        self._seal()
                    return True
            return False
        else:
            return self._executeControlWord(BQ27441_CONTROL_EXIT_CFGUPDATE)

    def flags(self):
        """
        Read the flags register.

        :return: 16-bit flags value
        """
        return self._readWord(BQ27441_COMMAND_FLAGS)

    def status(self):
        """
        Read the CONTROL_STATUS subcommand.

        :return: 16-bit status value
        """
        return self._readControlWord(BQ27441_CONTROL_STATUS)

    # -------------------------------------------------------------------------
    # Private: Seal / Unseal
    # -------------------------------------------------------------------------

    def _sealed(self):
        return bool(self.status() & BQ27441_STATUS_SS)

    def _seal(self):
        return self._readControlWord(BQ27441_CONTROL_SEALED)

    def _unseal(self):
        if self._readControlWord(BQ27441_UNSEAL_KEY):
            return self._readControlWord(BQ27441_UNSEAL_KEY)
        return False

    # -------------------------------------------------------------------------
    # Private: OpConfig
    # -------------------------------------------------------------------------

    def _opConfig(self):
        return self._readWord(BQ27441_EXTENDED_OPCONFIG)

    def _writeOpConfig(self, value):
        data = bytes([value >> 8, value & 0xFF])
        return self._writeExtendedData(BQ27441_ID_REGISTERS, 0, data)

    def _softReset(self):
        return self._executeControlWord(BQ27441_CONTROL_SOFT_RESET)

    # -------------------------------------------------------------------------
    # Private: Low-level word and control word access
    # -------------------------------------------------------------------------

    def _readWord(self, sub_address):
        try:
            data = self.i2c.readfrom_mem(self.address, sub_address, 2)
            return (data[1] << 8) | data[0]
        except:
            return 0

    def _readControlWord(self, function):
        try:
            cmd = bytes([function & 0xFF, (function >> 8) & 0xFF])
            self.i2c.writeto_mem(self.address, BQ27441_COMMAND_CONTROL, cmd)
            data = self.i2c.readfrom_mem(self.address, BQ27441_COMMAND_CONTROL, 2)
            return (data[1] << 8) | data[0]
        except:
            return 0

    def _executeControlWord(self, function):
        try:
            cmd = bytes([function & 0xFF, (function >> 8) & 0xFF])
            self.i2c.writeto_mem(self.address, BQ27441_COMMAND_CONTROL, cmd)
            return True
        except:
            return False

    # -------------------------------------------------------------------------
    # Private: Extended data block access
    # -------------------------------------------------------------------------

    def _blockDataControl(self):
        try:
            self.i2c.writeto_mem(self.address, BQ27441_EXTENDED_CONTROL, bytes([0x00]))
            return True
        except:
            return False

    def _blockDataClass(self, class_id):
        try:
            self.i2c.writeto_mem(self.address, BQ27441_EXTENDED_DATACLASS, bytes([class_id]))
            return True
        except:
            return False

    def _blockDataOffset(self, offset):
        try:
            self.i2c.writeto_mem(self.address, BQ27441_EXTENDED_DATABLOCK, bytes([offset]))
            return True
        except:
            return False

    def _blockDataChecksum(self):
        try:
            data = self.i2c.readfrom_mem(self.address, BQ27441_EXTENDED_CHECKSUM, 1)
            return data[0]
        except:
            return 0

    def _readBlockData(self, offset):
        try:
            addr = BQ27441_EXTENDED_BLOCKDATA + offset
            data = self.i2c.readfrom_mem(self.address, addr, 1)
            return data[0]
        except:
            return 0

    def _writeBlockData(self, offset, value):
        try:
            addr = BQ27441_EXTENDED_BLOCKDATA + offset
            self.i2c.writeto_mem(self.address, addr, bytes([value]))
            return True
        except:
            return False

    def _computeBlockChecksum(self):
        try:
            data = self.i2c.readfrom_mem(self.address, BQ27441_EXTENDED_BLOCKDATA, 32)
            csum = (255 - sum(data)) & 0xFF
            return csum
        except:
            return 0

    def _writeBlockChecksum(self, csum):
        try:
            self.i2c.writeto_mem(self.address, BQ27441_EXTENDED_CHECKSUM, bytes([csum]))
            return True
        except:
            return False

    def _readExtendedData(self, class_id, offset):
        """
        Read a single byte from extended data memory.

        :param class_id: Data class ID
        :param offset: Byte offset within the class
        :return: Byte value read
        """
        if not self._user_config_control:
            self.enterConfig(False)

        if not self._blockDataControl():
            return 0
        if not self._blockDataClass(class_id):
            return 0

        self._blockDataOffset(offset // 32)
        self._computeBlockChecksum()

        ret = self._readBlockData(offset % 32)

        if not self._user_config_control:
            self.exitConfig()

        return ret

    def _writeExtendedData(self, class_id, offset, data):
        """
        Write bytes to extended data memory.

        :param class_id: Data class ID
        :param offset: Byte offset within the class
        :param data: bytes object to write (max 32 bytes)
        :return: True on success
        """
        if len(data) > 32:
            return False

        if not self._user_config_control:
            self.enterConfig(False)

        if not self._blockDataControl():
            return False
        if not self._blockDataClass(class_id):
            return False

        self._blockDataOffset(offset // 32)
        self._computeBlockChecksum()

        for i, byte in enumerate(data):
            self._writeBlockData((offset % 32) + i, byte)

        new_csum = self._computeBlockChecksum()
        self._writeBlockChecksum(new_csum)

        if not self._user_config_control:
            self.exitConfig()

        return True


# Convenience instance — mirrors the Arduino library's global `lipo` object
lipo = BQ27441()