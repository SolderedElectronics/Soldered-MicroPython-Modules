# FILE: lsm9ds1.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython driver for LSM9DS1 9-axis IMU (accel/gyro/mag)
# LAST UPDATED: 2026-06-02

from machine import I2C, Pin
from os import uname
import struct
import time

# I2C addresses
_AG_ADDR = 0x6B
_M_ADDR  = 0x1E

# AG registers
_ACT_THS          = 0x04
_ACT_DUR          = 0x05
_INT_GEN_CFG_XL   = 0x06
_INT_GEN_THS_X_XL = 0x07
_INT_GEN_DUR_XL   = 0x0A
_INT1_CTRL        = 0x0C
_INT2_CTRL        = 0x0D
_WHO_AM_I_XG      = 0x0F
_CTRL_REG1_G      = 0x10
_CTRL_REG2_G      = 0x11
_CTRL_REG3_G      = 0x12
_ORIENT_CFG_G     = 0x13
_INT_GEN_SRC_G    = 0x14
_OUT_TEMP_L       = 0x15
_STATUS_REG_0     = 0x17
_OUT_X_L_G        = 0x18
_CTRL_REG4        = 0x1E
_CTRL_REG5_XL     = 0x1F
_CTRL_REG6_XL     = 0x20
_CTRL_REG7_XL     = 0x21
_CTRL_REG8        = 0x22
_CTRL_REG9        = 0x23
_INT_GEN_SRC_XL   = 0x26
_STATUS_REG_1     = 0x27
_OUT_X_L_XL       = 0x28
_FIFO_CTRL        = 0x2E
_FIFO_SRC         = 0x2F
_INT_GEN_CFG_G    = 0x30
_INT_GEN_THS_XH_G = 0x31
_INT_GEN_DUR_G    = 0x37

# Magnetometer registers
_WHO_AM_I_M   = 0x0F
_CTRL_REG1_M  = 0x20
_CTRL_REG2_M  = 0x21
_CTRL_REG3_M  = 0x22
_CTRL_REG4_M  = 0x23
_CTRL_REG5_M  = 0x24
_STATUS_REG_M = 0x27
_OUT_X_L_M    = 0x28
_INT_CFG_M    = 0x30
_INT_SRC_M    = 0x31
_INT_THS_L_M  = 0x32
_INT_THS_H_M  = 0x33

# Sensitivity constants (datasheet Table 3)
_SENS_ACCEL = {2: 0.000061, 4: 0.000122, 8: 0.000244, 16: 0.000732}
_SENS_GYRO  = {245: 0.00875, 500: 0.0175, 2000: 0.07}
_SENS_MAG   = {4: 0.00014, 8: 0.00029, 12: 0.00043, 16: 0.00058}

# Interrupt select
XG_INT1 = _INT1_CTRL
XG_INT2 = _INT2_CTRL

# Interrupt generators (OR these together)
INT_DRDY_XL    = 0x01
INT_DRDY_G     = 0x02
INT1_BOOT      = 0x04
INT2_DRDY_TEMP = 0x04
INT_FTH        = 0x08
INT_OVR        = 0x10
INT_FSS5       = 0x20
INT_IG_XL      = 0x40
INT1_IG_G      = 0x80
INT2_INACT     = 0x80

# Accelerometer interrupt generators
XLIE_XL = 0x01
XHIE_XL = 0x02
YLIE_XL = 0x04
YHIE_XL = 0x08
ZLIE_XL = 0x10
ZHIE_XL = 0x20
GEN_6D  = 0x40

# Gyroscope interrupt generators
XLIE_G = 0x01
XHIE_G = 0x02
YLIE_G = 0x04
YHIE_G = 0x08
ZLIE_G = 0x10
ZHIE_G = 0x20

# Magnetometer interrupt generators
ZIEN = 0x20
YIEN = 0x40
XIEN = 0x80

# Interrupt active level
INT_ACTIVE_HIGH = 0
INT_ACTIVE_LOW  = 1

# Interrupt output type
INT_PUSH_PULL  = 0
INT_OPEN_DRAIN = 1

# FIFO modes
FIFO_OFF          = 0
FIFO_THS          = 1
FIFO_CONT_TRIGGER = 3
FIFO_OFF_TRIGGER  = 4
FIFO_CONT         = 6

# Axes
X_AXIS   = 0
Y_AXIS   = 1
Z_AXIS   = 2
ALL_AXIS = 3


class _GyroSettings:
    def __init__(self):
        self.enabled        = True
        self.scale          = 245
        self.sampleRate     = 6
        self.bandwidth      = 0
        self.lowPowerEnable = False
        self.HPFEnable      = False
        self.HPFCutoff      = 0
        self.flipX          = False
        self.flipY          = False
        self.flipZ          = False
        self.enableX        = True
        self.enableY        = True
        self.enableZ        = True
        self.latchInterrupt = True


class _AccelSettings:
    def __init__(self):
        self.enabled          = True
        self.scale            = 2
        self.sampleRate       = 6
        self.enableX          = True
        self.enableY          = True
        self.enableZ          = True
        self.bandwidth        = -1
        self.highResEnable    = False
        self.highResBandwidth = 0


class _MagSettings:
    def __init__(self):
        self.enabled                = True
        self.scale                  = 4
        self.sampleRate             = 7
        self.tempCompensationEnable = False
        self.XYPerformance          = 3
        self.ZPerformance           = 3
        self.lowPowerEnable         = False
        self.operatingMode          = 0


class _TempSettings:
    def __init__(self):
        self.enabled = True


class IMUSettings:
    def __init__(self):
        self.gyro  = _GyroSettings()
        self.accel = _AccelSettings()
        self.mag   = _MagSettings()
        self.temp  = _TempSettings()


class LSM9DS1:
    """MicroPython driver for the LSM9DS1 9-axis IMU."""

    def __init__(self, i2c=None, auto_begin=True):
        """
        Initialize the LSM9DS1.

        :param i2c: I2C object; if None, auto-initializes on ESP32 (SCL=22, SDA=21)
        :param auto_begin: if True, call begin() immediately with default settings
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.settings = IMUSettings()

        self.ax = self.ay = self.az = 0
        self.gx = self.gy = self.gz = 0
        self.mx = self.my = self.mz = 0
        self.temperature = 0

        self.gBias    = [0.0, 0.0, 0.0]
        self.aBias    = [0.0, 0.0, 0.0]
        self.mBias    = [0.0, 0.0, 0.0]
        self.gBiasRaw = [0, 0, 0]
        self.aBiasRaw = [0, 0, 0]
        self.mBiasRaw = [0, 0, 0]
        self._autoCalc = False

        self.gRes = 0.0
        self.aRes = 0.0
        self.mRes = 0.0

        if auto_begin:
            self.begin()

    def begin(self):
        """
        Initialize sensor with current settings. Call after configuring settings if auto_begin=False.

        :returns: WHO_AM_I combined value (0x683D on success)
        """
        self._constrainScales()
        self._calcgRes()
        self._calcaRes()
        self._calcmRes()

        ag_id = self._readReg(_AG_ADDR, _WHO_AM_I_XG)
        m_id  = self._readReg(_M_ADDR,  _WHO_AM_I_M)

        if ag_id != 0x68 or m_id != 0x3D:
            raise Exception("LSM9DS1 not found! Check wiring.")

        self._initGyro()
        self._initAccel()
        self._initMag()

        return (ag_id << 8) | m_id

    def _initGyro(self):
        reg = 0
        if self.settings.gyro.enabled:
            reg = (self.settings.gyro.sampleRate & 0x07) << 5
        if self.settings.gyro.scale == 500:
            reg |= (0x1 << 3)
        elif self.settings.gyro.scale == 2000:
            reg |= (0x3 << 3)
        reg |= (self.settings.gyro.bandwidth & 0x3)
        self._writeReg(_AG_ADDR, _CTRL_REG1_G, reg)

        self._writeReg(_AG_ADDR, _CTRL_REG2_G, 0x00)

        reg = 0x80 if self.settings.gyro.lowPowerEnable else 0
        if self.settings.gyro.HPFEnable:
            reg |= 0x40 | (self.settings.gyro.HPFCutoff & 0x0F)
        self._writeReg(_AG_ADDR, _CTRL_REG3_G, reg)

        reg = 0
        if self.settings.gyro.enableZ:        reg |= 0x20
        if self.settings.gyro.enableY:        reg |= 0x10
        if self.settings.gyro.enableX:        reg |= 0x08
        if self.settings.gyro.latchInterrupt: reg |= 0x02
        self._writeReg(_AG_ADDR, _CTRL_REG4, reg)

        reg = 0
        if self.settings.gyro.flipX: reg |= 0x20
        if self.settings.gyro.flipY: reg |= 0x10
        if self.settings.gyro.flipZ: reg |= 0x08
        self._writeReg(_AG_ADDR, _ORIENT_CFG_G, reg)

    def _initAccel(self):
        reg = 0
        if self.settings.accel.enableZ: reg |= 0x20
        if self.settings.accel.enableY: reg |= 0x10
        if self.settings.accel.enableX: reg |= 0x08
        self._writeReg(_AG_ADDR, _CTRL_REG5_XL, reg)

        reg = 0
        if self.settings.accel.enabled:
            reg |= (self.settings.accel.sampleRate & 0x07) << 5
        scale = self.settings.accel.scale
        if scale == 4:    reg |= (0x2 << 3)
        elif scale == 8:  reg |= (0x3 << 3)
        elif scale == 16: reg |= (0x1 << 3)
        if self.settings.accel.bandwidth >= 0:
            reg |= 0x04 | (self.settings.accel.bandwidth & 0x03)
        self._writeReg(_AG_ADDR, _CTRL_REG6_XL, reg)

        reg = 0
        if self.settings.accel.highResEnable:
            reg |= 0x80 | ((self.settings.accel.highResBandwidth & 0x3) << 5)
        self._writeReg(_AG_ADDR, _CTRL_REG7_XL, reg)

    def _initMag(self):
        reg = 0
        if self.settings.mag.tempCompensationEnable: reg |= 0x80
        reg |= (self.settings.mag.XYPerformance & 0x3) << 5
        reg |= (self.settings.mag.sampleRate & 0x7) << 2
        self._writeReg(_M_ADDR, _CTRL_REG1_M, reg)

        reg = 0
        scale = self.settings.mag.scale
        if scale == 8:    reg |= (0x1 << 5)
        elif scale == 12: reg |= (0x2 << 5)
        elif scale == 16: reg |= (0x3 << 5)
        self._writeReg(_M_ADDR, _CTRL_REG2_M, reg)

        reg = 0
        if self.settings.mag.lowPowerEnable: reg |= 0x20
        reg |= (self.settings.mag.operatingMode & 0x3)
        self._writeReg(_M_ADDR, _CTRL_REG3_M, reg)

        self._writeReg(_M_ADDR, _CTRL_REG4_M, (self.settings.mag.ZPerformance & 0x3) << 2)
        self._writeReg(_M_ADDR, _CTRL_REG5_M, 0x00)

    def _constrainScales(self):
        if self.settings.gyro.scale not in (245, 500, 2000):
            self.settings.gyro.scale = 245
        if self.settings.accel.scale not in (2, 4, 8, 16):
            self.settings.accel.scale = 2
        if self.settings.mag.scale not in (4, 8, 12, 16):
            self.settings.mag.scale = 4

    def _calcgRes(self):
        self.gRes = _SENS_GYRO.get(self.settings.gyro.scale, _SENS_GYRO[245])

    def _calcaRes(self):
        self.aRes = _SENS_ACCEL.get(self.settings.accel.scale, _SENS_ACCEL[2])

    def _calcmRes(self):
        self.mRes = _SENS_MAG.get(self.settings.mag.scale, _SENS_MAG[4])

    # --- Available checks ---

    def accelAvailable(self):
        """
        :returns: bool, True if new accelerometer data ready
        """
        return bool(self._readReg(_AG_ADDR, _STATUS_REG_1) & 0x01)

    def gyroAvailable(self):
        """
        :returns: bool, True if new gyroscope data ready
        """
        return bool(self._readReg(_AG_ADDR, _STATUS_REG_1) & 0x02)

    def tempAvailable(self):
        """
        :returns: bool, True if new temperature data ready
        """
        return bool(self._readReg(_AG_ADDR, _STATUS_REG_1) & 0x04)

    def magAvailable(self, axis=ALL_AXIS):
        """
        :param axis: X_AXIS, Y_AXIS, Z_AXIS, or ALL_AXIS (default)
        :returns: bool, True if new magnetometer data ready on given axis
        """
        status = self._readReg(_M_ADDR, _STATUS_REG_M)
        if axis == ALL_AXIS:
            return bool(status & 0x07)
        return bool((status >> axis) & 0x01)

    # --- Read sensors ---

    def readAccel(self):
        """Read accelerometer, store raw signed int16 values in ax, ay, az."""
        data = self._readRegs(_AG_ADDR, _OUT_X_L_XL, 6)
        self.ax, self.ay, self.az = struct.unpack('<hhh', data)
        if self._autoCalc:
            self.ax -= self.aBiasRaw[0]
            self.ay -= self.aBiasRaw[1]
            self.az -= self.aBiasRaw[2]

    def readGyro(self):
        """Read gyroscope, store raw signed int16 values in gx, gy, gz."""
        data = self._readRegs(_AG_ADDR, _OUT_X_L_G, 6)
        self.gx, self.gy, self.gz = struct.unpack('<hhh', data)
        if self._autoCalc:
            self.gx -= self.gBiasRaw[0]
            self.gy -= self.gBiasRaw[1]
            self.gz -= self.gBiasRaw[2]

    def readMag(self):
        """Read magnetometer, store raw signed int16 values in mx, my, mz."""
        data = self._readRegs(_M_ADDR, _OUT_X_L_M, 6)
        self.mx, self.my, self.mz = struct.unpack('<hhh', data)

    def readTemp(self):
        """Read temperature sensor, store result in self.temperature (degrees C)."""
        data = self._readRegs(_AG_ADDR, _OUT_TEMP_L, 2)
        raw = struct.unpack('<h', data)[0]
        self.temperature = 25 + (raw >> 8)

    # --- Calc (raw to physical units) ---

    def calcAccel(self, raw):
        """
        Convert raw accelerometer reading to g's.

        :param raw: int16 raw value (ax, ay, or az)
        :returns: float in g
        """
        return self.aRes * raw

    def calcGyro(self, raw):
        """
        Convert raw gyroscope reading to degrees/second.

        :param raw: int16 raw value (gx, gy, or gz)
        :returns: float in dps
        """
        return self.gRes * raw

    def calcMag(self, raw):
        """
        Convert raw magnetometer reading to Gauss.

        :param raw: int16 raw value (mx, my, or mz)
        :returns: float in Gauss
        """
        return self.mRes * raw

    # --- Scale / ODR setters ---

    def setGyroScale(self, scale):
        """
        Set gyroscope full-scale range.

        :param scale: 245, 500, or 2000 (dps)
        """
        reg = self._readReg(_AG_ADDR, _CTRL_REG1_G) & 0xE7
        if scale == 500:
            reg |= (0x1 << 3)
            self.settings.gyro.scale = 500
        elif scale == 2000:
            reg |= (0x3 << 3)
            self.settings.gyro.scale = 2000
        else:
            self.settings.gyro.scale = 245
        self._writeReg(_AG_ADDR, _CTRL_REG1_G, reg)
        self._calcgRes()

    def setAccelScale(self, scale):
        """
        Set accelerometer full-scale range.

        :param scale: 2, 4, 8, or 16 (g)
        """
        reg = self._readReg(_AG_ADDR, _CTRL_REG6_XL) & 0xE7
        if scale == 4:
            reg |= (0x2 << 3)
            self.settings.accel.scale = 4
        elif scale == 8:
            reg |= (0x3 << 3)
            self.settings.accel.scale = 8
        elif scale == 16:
            reg |= (0x1 << 3)
            self.settings.accel.scale = 16
        else:
            self.settings.accel.scale = 2
        self._writeReg(_AG_ADDR, _CTRL_REG6_XL, reg)
        self._calcaRes()

    def setMagScale(self, scale):
        """
        Set magnetometer full-scale range.

        :param scale: 4, 8, 12, or 16 (Gauss)
        """
        reg = self._readReg(_M_ADDR, _CTRL_REG2_M) & 0x9F
        if scale == 8:
            reg |= (0x1 << 5)
            self.settings.mag.scale = 8
        elif scale == 12:
            reg |= (0x2 << 5)
            self.settings.mag.scale = 12
        elif scale == 16:
            reg |= (0x3 << 5)
            self.settings.mag.scale = 16
        else:
            self.settings.mag.scale = 4
        self._writeReg(_M_ADDR, _CTRL_REG2_M, reg)
        self._calcmRes()

    def setGyroODR(self, rate):
        """
        Set gyroscope output data rate.

        :param rate: 1-6 (14.9 / 59.5 / 119 / 238 / 476 / 952 Hz)
        """
        if rate & 0x07:
            reg = (self._readReg(_AG_ADDR, _CTRL_REG1_G) & 0x1F) | ((rate & 0x07) << 5)
            self.settings.gyro.sampleRate = rate & 0x07
            self._writeReg(_AG_ADDR, _CTRL_REG1_G, reg)

    def setAccelODR(self, rate):
        """
        Set accelerometer output data rate.

        :param rate: 1-6 (10 / 50 / 119 / 238 / 476 / 952 Hz)
        """
        if rate & 0x07:
            reg = (self._readReg(_AG_ADDR, _CTRL_REG6_XL) & 0x1F) | ((rate & 0x07) << 5)
            self.settings.accel.sampleRate = rate & 0x07
            self._writeReg(_AG_ADDR, _CTRL_REG6_XL, reg)

    def setMagODR(self, rate):
        """
        Set magnetometer output data rate.

        :param rate: 0-7 (0.625 / 1.25 / 2.5 / 5 / 10 / 20 / 40 / 80 Hz)
        """
        reg = (self._readReg(_M_ADDR, _CTRL_REG1_M) & 0xE3) | ((rate & 0x07) << 2)
        self.settings.mag.sampleRate = rate & 0x07
        self._writeReg(_M_ADDR, _CTRL_REG1_M, reg)

    # --- Sample rate helpers ---

    def accelerationSampleRate(self):
        """
        :returns: float, accelerometer sample rate in Hz
        """
        rates = {1: 10.0, 2: 50.0, 3: 119.0, 4: 238.0, 5: 476.0, 6: 952.0}
        return rates.get(self.settings.accel.sampleRate, 0.0)

    def gyroscopeSampleRate(self):
        """
        :returns: float, gyroscope sample rate in Hz
        """
        rates = {1: 14.9, 2: 59.5, 3: 119.0, 4: 238.0, 5: 476.0, 6: 952.0}
        return rates.get(self.settings.gyro.sampleRate, 0.0)

    def magneticFieldSampleRate(self):
        """
        :returns: float, magnetometer sample rate in Hz
        """
        rates = {0: 0.625, 1: 1.25, 2: 2.5, 3: 5.0, 4: 10.0, 5: 20.0, 6: 40.0, 7: 80.0}
        return rates.get(self.settings.mag.sampleRate, 0.0)

    # --- Interrupt configuration ---

    def configInt(self, interrupt, generator, activeLow=INT_ACTIVE_LOW, pushPull=INT_PUSH_PULL):
        """
        Configure INT1 or INT2 interrupt output.

        :param interrupt: XG_INT1 or XG_INT2
        :param generator: OR'd combination of interrupt generator values
        :param activeLow: INT_ACTIVE_LOW or INT_ACTIVE_HIGH
        :param pushPull: INT_PUSH_PULL or INT_OPEN_DRAIN
        """
        self._writeReg(_AG_ADDR, interrupt, generator)
        reg = self._readReg(_AG_ADDR, _CTRL_REG8)
        if activeLow:
            reg |= 0x20
        else:
            reg &= ~0x20
        if pushPull:
            reg &= ~0x10
        else:
            reg |= 0x10
        self._writeReg(_AG_ADDR, _CTRL_REG8, reg & 0xFF)

    def configAccelInt(self, generator, andInterrupts=False):
        """
        Configure accelerometer interrupt generator.

        :param generator: OR'd combination of XHIE_XL/XLIE_XL/YHIE_XL/etc.
        :param andInterrupts: True = AND combination, False = OR
        """
        self._writeReg(_AG_ADDR, _INT_GEN_CFG_XL, generator | (0x80 if andInterrupts else 0))

    def configAccelThs(self, threshold, axis, duration=0, wait=False):
        """
        Configure accelerometer interrupt threshold.

        :param threshold: 0-255, raw threshold (equivalent raw accel = threshold * 128)
        :param axis: X_AXIS, Y_AXIS, or Z_AXIS
        :param duration: samples threshold must be exceeded before interrupt fires
        :param wait: if True, wait duration samples before clearing interrupt
        """
        self._writeReg(_AG_ADDR, _INT_GEN_THS_X_XL + axis, threshold)
        self._writeReg(_AG_ADDR, _INT_GEN_DUR_XL, (duration & 0x7F) | (0x80 if wait else 0))

    def configGyroInt(self, generator, aoi, latch):
        """
        Configure gyroscope interrupt generator.

        :param generator: OR'd combination of ZHIE_G/YHIE_G/XHIE_G/etc.
        :param aoi: True = AND combination, False = OR
        :param latch: True to latch interrupt until cleared
        """
        reg = generator
        if aoi:   reg |= 0x80
        if latch: reg |= 0x40
        self._writeReg(_AG_ADDR, _INT_GEN_CFG_G, reg)

    def configGyroThs(self, threshold, axis, duration, wait):
        """
        Configure gyroscope interrupt threshold.

        :param threshold: 0-0x7FFF, raw gyroscope value
        :param axis: X_AXIS, Y_AXIS, or Z_AXIS
        :param duration: samples threshold must be exceeded
        :param wait: if True, wait duration samples before clearing
        """
        self._writeReg(_AG_ADDR, _INT_GEN_THS_XH_G + (axis * 2),      (threshold >> 8) & 0x7F)
        self._writeReg(_AG_ADDR, _INT_GEN_THS_XH_G + (axis * 2) + 1,   threshold & 0xFF)
        self._writeReg(_AG_ADDR, _INT_GEN_DUR_G, (duration & 0x7F) | (0x80 if wait else 0))

    def configMagInt(self, generator, activeLow, latch=True):
        """
        Configure magnetometer interrupt.

        :param generator: OR'd combination of XIEN/YIEN/ZIEN
        :param activeLow: INT_ACTIVE_LOW or INT_ACTIVE_HIGH
        :param latch: True to latch interrupt
        """
        config = generator & 0xE0
        if activeLow == INT_ACTIVE_HIGH: config |= 0x04
        if not latch:                    config |= 0x02
        if generator:                    config |= 0x01
        self._writeReg(_M_ADDR, _INT_CFG_M, config)

    def configMagThs(self, threshold):
        """
        Configure magnetometer interrupt threshold.

        :param threshold: 0-0x7FFF, raw magnetometer value
        """
        self._writeReg(_M_ADDR, _INT_THS_H_M, (threshold >> 8) & 0x7F)
        self._writeReg(_M_ADDR, _INT_THS_L_M,  threshold & 0xFF)

    def configInactivity(self, duration, threshold, sleepOn):
        """
        Configure inactivity interrupt parameters.

        :param duration: inactivity duration (ODR-dependent)
        :param threshold: activity threshold 0-127
        :param sleepOn: True = sleep gyro on inactivity, False = power down
        """
        self._writeReg(_AG_ADDR, _ACT_THS, (threshold & 0x7F) | (0x80 if sleepOn else 0))
        self._writeReg(_AG_ADDR, _ACT_DUR, duration)

    def getGyroIntSrc(self):
        """
        :returns: gyroscope interrupt source register value, 0 if interrupt not active
        """
        src = self._readReg(_AG_ADDR, _INT_GEN_SRC_G)
        return (src & 0x3F) if (src & 0x40) else 0

    def getAccelIntSrc(self):
        """
        :returns: accelerometer interrupt source register value, 0 if interrupt not active
        """
        src = self._readReg(_AG_ADDR, _INT_GEN_SRC_XL)
        return (src & 0x3F) if (src & 0x40) else 0

    def getMagIntSrc(self):
        """
        :returns: magnetometer interrupt source register value, 0 if interrupt not active
        """
        src = self._readReg(_M_ADDR, _INT_SRC_M)
        return (src & 0xFE) if (src & 0x01) else 0

    def getInactivity(self):
        """
        :returns: inactivity interrupt status byte
        """
        return self._readReg(_AG_ADDR, _STATUS_REG_0) & 0x10

    # --- FIFO ---

    def enableFIFO(self, enable=True):
        """
        Enable or disable the FIFO.

        :param enable: True to enable, False to disable
        """
        reg = self._readReg(_AG_ADDR, _CTRL_REG9)
        reg = (reg | 0x02) if enable else (reg & ~0x02)
        self._writeReg(_AG_ADDR, _CTRL_REG9, reg & 0xFF)

    def setFIFO(self, mode, threshold):
        """
        Configure FIFO mode and threshold.

        :param mode: FIFO_OFF, FIFO_THS, FIFO_CONT, FIFO_CONT_TRIGGER, or FIFO_OFF_TRIGGER
        :param threshold: 0-31
        """
        self._writeReg(_AG_ADDR, _FIFO_CTRL, ((mode & 0x7) << 5) | min(threshold, 0x1F))

    def getFIFOSamples(self):
        """
        :returns: int, number of samples currently in FIFO
        """
        return self._readReg(_AG_ADDR, _FIFO_SRC) & 0x3F

    # --- Gyro sleep ---

    def sleepGyro(self, enable=True):
        """
        Sleep or wake the gyroscope.

        :param enable: True to sleep gyro, False to wake
        """
        reg = self._readReg(_AG_ADDR, _CTRL_REG9)
        reg = (reg | 0x40) if enable else (reg & ~0x40)
        self._writeReg(_AG_ADDR, _CTRL_REG9, reg & 0xFF)

    # --- Calibration ---

    def calibrate(self, autoCalc=True):
        """
        Collect 32 FIFO samples of accel/gyro and compute bias offsets.

        :param autoCalc: if True, bias is automatically subtracted from future reads
        """
        gBiasTemp = [0, 0, 0]
        aBiasTemp = [0, 0, 0]

        self.enableFIFO(True)
        self.setFIFO(FIFO_THS, 0x1F)
        while self.getFIFOSamples() < 0x1F:
            pass

        samples = self.getFIFOSamples()
        for _ in range(samples):
            self.readGyro()
            gBiasTemp[0] += self.gx
            gBiasTemp[1] += self.gy
            gBiasTemp[2] += self.gz
            self.readAccel()
            aBiasTemp[0] += self.ax
            aBiasTemp[1] += self.ay
            aBiasTemp[2] += self.az - int(1.0 / self.aRes)

        for i in range(3):
            self.gBiasRaw[i] = gBiasTemp[i] // samples
            self.gBias[i]    = self.calcGyro(self.gBiasRaw[i])
            self.aBiasRaw[i] = aBiasTemp[i] // samples
            self.aBias[i]    = self.calcAccel(self.aBiasRaw[i])

        self.enableFIFO(False)
        self.setFIFO(FIFO_OFF, 0x00)

        if autoCalc:
            self._autoCalc = True

    def calibrateMag(self, loadIn=True):
        """
        Collect 128 magnetometer samples and compute hard-iron offset bias.

        :param loadIn: if True, write offsets to sensor hardware offset registers
        """
        magMin = [0, 0, 0]
        magMax = [0, 0, 0]

        for _ in range(128):
            while not self.magAvailable():
                pass
            self.readMag()
            for j, v in enumerate([self.mx, self.my, self.mz]):
                if v > magMax[j]: magMax[j] = v
                if v < magMin[j]: magMin[j] = v

        for j in range(3):
            self.mBiasRaw[j] = (magMax[j] + magMin[j]) // 2
            self.mBias[j]    = self.calcMag(self.mBiasRaw[j])
            if loadIn:
                self._magOffset(j, self.mBiasRaw[j])

    def _magOffset(self, axis, offset):
        base = 0x05
        self._writeReg(_M_ADDR, base + (2 * axis),      offset & 0xFF)
        self._writeReg(_M_ADDR, base + (2 * axis) + 1, (offset >> 8) & 0xFF)

    # --- Low-level I2C ---

    def _readReg(self, addr, reg):
        try:
            return self.i2c.readfrom_mem(addr, reg, 1)[0]
        except OSError as e:
            raise Exception("I2C read error: {}".format(e))

    def _readRegs(self, addr, reg, length):
        # 0x80 | reg sets auto-increment bit required by LSM9DS1 for multi-byte reads
        try:
            return self.i2c.readfrom_mem(addr, 0x80 | reg, length)
        except OSError as e:
            raise Exception("I2C read error: {}".format(e))

    def _writeReg(self, addr, reg, value):
        try:
            self.i2c.writeto_mem(addr, reg, bytes([value]))
        except OSError as e:
            raise Exception("I2C write error: {}".format(e))
