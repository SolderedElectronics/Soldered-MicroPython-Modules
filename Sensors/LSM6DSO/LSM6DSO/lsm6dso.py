# FILE: lsm6dso.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython driver for LSM6DSO/LSM6DSO32 6-axis IMU (accelerometer/gyroscope)
# LAST UPDATED: 2026-07-02

from machine import I2C, Pin
from os import uname
import struct
import time

# I2C address (fixed, SA0 = 1)
DEFAULT_ADDR = 0x6B

# Interrupt pin selectors
INT1_PIN = 1
INT2_PIN = 2

# Detected chip variant (returned by getVariant())
VARIANT_LSM6DSO = 0
VARIANT_LSM6DSO32 = 1

# Tap threshold presets (5-bit field, 0-31)
TAP_THRESHOLD_LOW = 0x01
TAP_THRESHOLD_MID_LOW = 0x08
TAP_THRESHOLD_MID = 0x10
TAP_THRESHOLD_MID_HIGH = 0x18
TAP_THRESHOLD_HIGH = 0x1F

# Tap shock time presets (2-bit field)
TAP_SHOCK_TIME_LOW = 0x00
TAP_SHOCK_TIME_MID_LOW = 0x01
TAP_SHOCK_TIME_MID_HIGH = 0x02
TAP_SHOCK_TIME_HIGH = 0x03

# Tap quiet time presets (2-bit field)
TAP_QUIET_TIME_LOW = 0x00
TAP_QUIET_TIME_MID_LOW = 0x01
TAP_QUIET_TIME_MID_HIGH = 0x02
TAP_QUIET_TIME_HIGH = 0x03

# Tap duration time presets (4-bit field)
TAP_DURATION_TIME_LOW = 0x00
TAP_DURATION_TIME_MID_LOW = 0x04
TAP_DURATION_TIME_MID = 0x08
TAP_DURATION_TIME_MID_HIGH = 0x0C
TAP_DURATION_TIME_HIGH = 0x0F

# Wake-up threshold presets (6-bit field, 0-63)
WAKE_UP_THRESHOLD_LOW = 0x01
WAKE_UP_THRESHOLD_MID_LOW = 0x0F
WAKE_UP_THRESHOLD_MID = 0x1F
WAKE_UP_THRESHOLD_MID_HIGH = 0x2F
WAKE_UP_THRESHOLD_HIGH = 0x3F

# Free-fall threshold presets (datasheet mg values)
FF_THRESHOLD_156MG = 0x00
FF_THRESHOLD_219MG = 0x01
FF_THRESHOLD_250MG = 0x02
FF_THRESHOLD_312MG = 0x03
FF_THRESHOLD_344MG = 0x04
FF_THRESHOLD_406MG = 0x05
FF_THRESHOLD_469MG = 0x06
FF_THRESHOLD_500MG = 0x07

# 6D orientation threshold presets (degrees from horizontal)
DEG_80 = 0x00
DEG_70 = 0x01
DEG_60 = 0x02
DEG_50 = 0x03

# --- Registers (user bank) ---
_WHO_AM_I = 0x0F
_WHO_AM_I_VAL = 0x6C

_FUNC_CFG_ACCESS = 0x01
_FIFO_CTRL4 = 0x0A

_CTRL1_XL = 0x10
_CTRL2_G = 0x11
_CTRL3_C = 0x12
_CTRL9_XL = 0x18

_WAKE_UP_SRC = 0x1B
_TAP_SRC = 0x1C
_D6D_SRC = 0x1D

_OUTX_L_G = 0x22
_OUTX_L_XL = 0x28

_TAP_CFG0 = 0x56
_TAP_CFG1 = 0x57
_TAP_CFG2 = 0x58
_TAP_THS_6D = 0x59
_INT_DUR2 = 0x5A
_WAKE_UP_THS = 0x5B
_WAKE_UP_DUR = 0x5C
_FREE_FALL = 0x5D
_MD1_CFG = 0x5E
_MD2_CFG = 0x5F

# Embedded-function bank (behind _FUNC_CFG_ACCESS)
_BANK_USER = 0x00
_BANK_EMBEDDED = 0x80

_PAGE_SEL = 0x02
_EMB_FUNC_EN_A = 0x04
_PAGE_ADDRESS = 0x08
_PAGE_VALUE = 0x09
_EMB_FUNC_INT1 = 0x0A
_EMB_FUNC_INT2 = 0x0E
_EMB_FUNC_STATUS = 0x12
_PAGE_RW = 0x17
_STEP_COUNTER_L = 0x62
_EMB_FUNC_SRC = 0x64

# Pedometer command register, only reachable through the page mechanism above
_PEDO_CMD_REG = 0x183

# ODR lookup tables (Hz -> CTRL1_XL/CTRL2_G bits[7:4], identical enum for XL/G)
_XL_ODR_STEPS = (12.5, 26, 52, 104, 208, 417, 833, 1667, 3333, 6667)
_G_ODR_STEPS = _XL_ODR_STEPS
_ODR_XL_MAP = {
    0: 0x00, 12.5: 0x10, 26: 0x20, 52: 0x30, 104: 0x40,
    208: 0x50, 417: 0x60, 833: 0x70, 1667: 0x80, 3333: 0x90, 6667: 0xA0,
}
_ODR_G_MAP = dict(_ODR_XL_MAP)
_ODR_XL_MAP_REV = {v: k for k, v in _ODR_XL_MAP.items()}
_ODR_G_MAP_REV = {v: k for k, v in _ODR_G_MAP.items()}

# Accelerometer full-scale register codes are the same for both variants,
# only the physical g-range they map to changes.
_FS_XL_CODE_LSM6DSO = {2: 0x00, 16: 0x04, 4: 0x08, 8: 0x0C}
_FS_XL_CODE_LSM6DSO_REV = {v: k for k, v in _FS_XL_CODE_LSM6DSO.items()}
_FS_XL_CODE_LSM6DSO32 = {4: 0x00, 32: 0x04, 8: 0x0C}
_FS_XL_CODE_LSM6DSO32_REV = {v: k for k, v in _FS_XL_CODE_LSM6DSO32.items()}
_ACC_SENSITIVITY = {2: 0.061, 4: 0.122, 8: 0.244, 16: 0.488, 32: 0.976}

# Gyroscope full scale (not affected by variant)
_FS_G_MAP = {245: 0x00, 500: 0x04, 1000: 0x08, 2000: 0x0C}
_FS_G_MAP_REV = {v: k for k, v in _FS_G_MAP.items()}
_GYRO_SENSITIVITY = {125: 4.375, 245: 8.750, 500: 17.500, 1000: 35.000, 2000: 70.000}


def _pickStep(value, steps):
    for s in steps:
        if value <= s:
            return s
    return steps[-1]


class LSM6DSO:
    """MicroPython driver for the LSM6DSO/LSM6DSO32 6-axis IMU (I2C only)."""

    def __init__(self, i2c=None, address=DEFAULT_ADDR):
        """
        Initialize the LSM6DSO sensor.

        :param i2c: Initialized I2C object (default None = auto-detect)
        :param address: I2C address of the sensor
        """
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.address = address
        self._xEnabled = False
        self._xLastOdr = 104
        self._gEnabled = False
        self._gLastOdr = 104
        self._variant = VARIANT_LSM6DSO

        if self.readId() != _WHO_AM_I_VAL:
            raise Exception("LSM6DSO initialization failed! Check wiring.")

        if not self.begin():
            raise Exception("LSM6DSO initialization failed! Check wiring.")

    # --- Lifecycle ---

    def begin(self) -> bool:
        """
        Configure the sensor with default settings (accel/gyro disabled, 2g/2000dps)
        and detect whether the chip is a plain LSM6DSO or an LSM6DSO32.

        :returns: bool, True on success
        """
        self._updateReg(_CTRL9_XL, 0x02, 0x02)  # I3C_DISABLE
        self._updateReg(_CTRL3_C, 0x04, 0x04)  # IF_INC enabled
        self._updateReg(_CTRL3_C, 0x40, 0x40)  # BDU enabled
        self._updateReg(_FIFO_CTRL4, 0x07, 0x00)  # FIFO bypass

        self._updateReg(_CTRL1_XL, 0xF0, 0x00)  # ODR_XL power down
        self._variant = self._detectVariant()
        self.setAcceleratorFullScale(4 if self._variant == VARIANT_LSM6DSO32 else 2)

        self._updateReg(_CTRL2_G, 0xF0, 0x00)  # ODR_G power down
        self.setGyroFullScale(2000)

        self._xLastOdr = 104
        self._xEnabled = False
        self._gLastOdr = 104
        self._gEnabled = False

        return True

    def end(self) -> bool:
        """
        Disable both accelerometer and gyroscope.

        :returns: bool, True on success
        """
        self.disableAccelerator()
        self.disableGyro()
        return True

    def enableAccelerator(self) -> bool:
        """
        Enable the accelerometer at its last configured ODR.

        :returns: bool, True on success
        """
        if self._xEnabled:
            return True
        self._updateReg(_CTRL1_XL, 0xF0, _ODR_XL_MAP[self._xLastOdr])
        self._xEnabled = True
        return True

    def disableAccelerator(self) -> bool:
        """
        Disable the accelerometer (power down).

        :returns: bool, True on success
        """
        if not self._xEnabled:
            return True
        self._xLastOdr = self.getAcceleratorOdr()
        self._updateReg(_CTRL1_XL, 0xF0, 0x00)
        self._xEnabled = False
        return True

    def enableGyro(self) -> bool:
        """
        Enable the gyroscope at its last configured ODR.

        :returns: bool, True on success
        """
        if self._gEnabled:
            return True
        self._updateReg(_CTRL2_G, 0xF0, _ODR_G_MAP[self._gLastOdr])
        self._gEnabled = True
        return True

    def disableGyro(self) -> bool:
        """
        Disable the gyroscope (power down).

        :returns: bool, True on success
        """
        if not self._gEnabled:
            return True
        self._gLastOdr = self.getGyroOdr()
        self._updateReg(_CTRL2_G, 0xF0, 0x00)
        self._gEnabled = False
        return True

    def readId(self) -> int:
        """
        Read the WHO_AM_I register.

        :returns: int, chip ID (expected 0x6C, shared by LSM6DSO and LSM6DSO32)
        """
        return self._readReg(_WHO_AM_I)

    def getVariant(self) -> int:
        """
        Get the chip variant detected during begin().

        :returns: int, VARIANT_LSM6DSO or VARIANT_LSM6DSO32
        """
        return self._variant

    def _detectVariant(self) -> int:
        """
        Detect LSM6DSO vs LSM6DSO32. Both share WHO_AM_I=0x6C, so the actual
        sensitivity is measured by briefly forcing a full-scale code and
        comparing the resulting raw 1g reading against the two possible
        physical ranges that code maps to.

        :returns: int, VARIANT_LSM6DSO or VARIANT_LSM6DSO32
        """
        curFsCode = self._readReg(_CTRL1_XL) & 0x0C
        wasEnabled = self._xEnabled
        if not wasEnabled:
            self._updateReg(_CTRL1_XL, 0xF0, 0x10)  # 12.5Hz, just to get samples

        def _sampleMax(fsCode):
            self._updateReg(_CTRL1_XL, 0x0C, fsCode)
            time.sleep_ms(100)
            peak = 0
            for _ in range(5):
                for r in self.getAcceleratorAxesRaw():
                    a = -r if r < 0 else r
                    if a > peak:
                        peak = a
                time.sleep_ms(20)
            return peak

        # FS code 0x04: 16g on LSM6DSO, 32g on LSM6DSO32
        peak = _sampleMax(0x04)
        if peak > 500:
            variant = VARIANT_LSM6DSO32 if peak < 1500 else VARIANT_LSM6DSO
        else:
            # Fallback, FS code 0x00: 2g on LSM6DSO, 4g on LSM6DSO32
            peak = _sampleMax(0x00)
            if peak > 500:
                variant = VARIANT_LSM6DSO32 if peak < 12000 else VARIANT_LSM6DSO
            else:
                variant = VARIANT_LSM6DSO

        self._updateReg(_CTRL1_XL, 0x0C, curFsCode)
        if not wasEnabled:
            self._updateReg(_CTRL1_XL, 0xF0, 0x00)

        return variant

    # --- Accelerometer / gyroscope data ---

    def getAcceleratorAxes(self) -> tuple:
        """
        Read accelerometer axes, scaled to mg.

        :returns: tuple(x, y, z) as int mg
        """
        raw = self.getAcceleratorAxesRaw()
        sens = self.getAcceleratorSensitivity()
        return tuple(int(r * sens) for r in raw)

    def getGyroAxes(self) -> tuple:
        """
        Read gyroscope axes, scaled to mdps.

        :returns: tuple(x, y, z) as int mdps
        """
        raw = self.getGyroAxesRaw()
        sens = self.getGyroSensitivity()
        return tuple(int(r * sens) for r in raw)

    def getAcceleratorAxesRaw(self) -> tuple:
        """
        Read raw accelerometer axes.

        :returns: tuple(x, y, z) as int16
        """
        data = self._readRegs(_OUTX_L_XL, 6)
        return struct.unpack("<3h", data)

    def getGyroAxesRaw(self) -> tuple:
        """
        Read raw gyroscope axes.

        :returns: tuple(x, y, z) as int16
        """
        data = self._readRegs(_OUTX_L_G, 6)
        return struct.unpack("<3h", data)

    def getAcceleratorSensitivity(self) -> float:
        """
        Get accelerometer sensitivity for the currently configured full scale.

        :returns: float, sensitivity in mg/LSB
        """
        fs = self.getAcceleratorFullScale()
        return _ACC_SENSITIVITY[int(fs)]

    def getGyroSensitivity(self) -> float:
        """
        Get gyroscope sensitivity for the currently configured full scale.

        :returns: float, sensitivity in mdps/LSB
        """
        fs = self.getGyroFullScale()
        return _GYRO_SENSITIVITY[int(fs)]

    # --- Output data rate ---

    def getAcceleratorOdr(self) -> float:
        """
        Get the accelerometer output data rate.

        :returns: float, ODR in Hz
        """
        bits = self._readReg(_CTRL1_XL) & 0xF0
        return float(_ODR_XL_MAP_REV[bits])

    def setAcceleratorOdr(self, odr: float) -> bool:
        """
        Set the accelerometer output data rate.

        :param odr: float, requested ODR in Hz (snapped to nearest supported rate)
        :returns: bool, True on success
        """
        step = _pickStep(odr, _XL_ODR_STEPS)
        if self._xEnabled:
            self._updateReg(_CTRL1_XL, 0xF0, _ODR_XL_MAP[step])
        else:
            self._xLastOdr = step
        return True

    def getGyroOdr(self) -> float:
        """
        Get the gyroscope output data rate.

        :returns: float, ODR in Hz
        """
        bits = self._readReg(_CTRL2_G) & 0xF0
        return float(_ODR_G_MAP_REV[bits])

    def setGyroOdr(self, odr: float) -> bool:
        """
        Set the gyroscope output data rate.

        :param odr: float, requested ODR in Hz (snapped to nearest supported rate)
        :returns: bool, True on success
        """
        step = _pickStep(odr, _G_ODR_STEPS)
        if self._gEnabled:
            self._updateReg(_CTRL2_G, 0xF0, _ODR_G_MAP[step])
        else:
            self._gLastOdr = step
        return True

    # --- Full scale ---

    def getAcceleratorFullScale(self) -> float:
        """
        Get the accelerometer full scale (physical range depends on variant).

        :returns: float, full scale in g
        """
        code = self._readReg(_CTRL1_XL) & 0x0C
        if self._variant == VARIANT_LSM6DSO32:
            return float(_FS_XL_CODE_LSM6DSO32_REV[code])
        return float(_FS_XL_CODE_LSM6DSO_REV[code])

    def setAcceleratorFullScale(self, fullScale: float) -> bool:
        """
        Set the accelerometer full scale.

        :param fullScale: float, requested full scale in g (snapped to the
            nearest supported range for the detected variant: 2/4/8/16 on
            LSM6DSO, 4/8/32 on LSM6DSO32)
        :returns: bool, True on success
        """
        if self._variant == VARIANT_LSM6DSO32:
            fs = 4 if fullScale <= 4.0 else 8 if fullScale <= 8.0 else 32
            code = _FS_XL_CODE_LSM6DSO32[fs]
        else:
            fs = 2 if fullScale <= 2.0 else 4 if fullScale <= 4.0 else 8 if fullScale <= 8.0 else 16
            code = _FS_XL_CODE_LSM6DSO[fs]
        self._updateReg(_CTRL1_XL, 0x0C, code)
        return True

    def getGyroFullScale(self) -> float:
        """
        Get the gyroscope full scale.

        :returns: float, full scale in dps
        """
        if self._readReg(_CTRL2_G) & 0x02:
            return 125.0
        bits = self._readReg(_CTRL2_G) & 0x0C
        return float(_FS_G_MAP_REV[bits])

    def setGyroFullScale(self, fullScale: float) -> bool:
        """
        Set the gyroscope full scale.

        :param fullScale: float, requested full scale in dps (snapped to 125/245/500/1000/2000)
        :returns: bool, True on success
        """
        if fullScale <= 125.0:
            self._updateReg(_CTRL2_G, 0x02, 0x02)
        else:
            fs = 245 if fullScale <= 245.0 else 500 if fullScale <= 500.0 else 1000 if fullScale <= 1000.0 else 2000
            self._updateReg(_CTRL2_G, 0x02, 0x00)
            self._updateReg(_CTRL2_G, 0x0C, _FS_G_MAP[fs])
        return True

    # --- Free-fall detection ---

    def enableFreeFallDetection(self, int_pin: int = INT1_PIN) -> bool:
        """
        Enable free-fall detection (sets accel ODR to 417Hz, full scale to 2g).

        :param int_pin: int, INT1_PIN or INT2_PIN
        :returns: bool, True on success
        """
        self.setAcceleratorOdr(417.0)
        self.setAcceleratorFullScale(2.0)
        self._updateReg(_FREE_FALL, 0xF8, 0x06 << 3)  # FF_DUR[4:0] = 6
        self._updateReg(_WAKE_UP_DUR, 0x80, 0x00)  # FF_DUR[5] = 0
        self._updateReg(_WAKE_UP_DUR, 0x60, 0x00)  # WAKE_DUR = 0
        self._updateReg(_WAKE_UP_DUR, 0x0F, 0x00)  # SLEEP_DUR = 0
        self._updateReg(_FREE_FALL, 0x07, FF_THRESHOLD_312MG)

        if int_pin == INT1_PIN:
            self._updateReg(_MD1_CFG, 0x10, 0x10)
        elif int_pin == INT2_PIN:
            self._updateReg(_MD2_CFG, 0x10, 0x10)
        else:
            return False
        self._updateInterruptsEnable()
        return True

    def disableFreeFallDetection(self) -> bool:
        """
        Disable free-fall detection.

        :returns: bool, True on success
        """
        self._updateReg(_MD1_CFG, 0x10, 0x00)
        self._updateReg(_MD2_CFG, 0x10, 0x00)
        self._updateReg(_FREE_FALL, 0xF8, 0x00)
        self._updateReg(_FREE_FALL, 0x07, FF_THRESHOLD_156MG)
        self._updateInterruptsEnable()
        return True

    def setFreeFallThreshold(self, thr: int) -> bool:
        """
        Set the free-fall detection threshold.

        :param thr: int, one of the FF_THRESHOLD_* presets
        :returns: bool, True on success
        """
        self._updateReg(_FREE_FALL, 0x07, thr & 0x07)
        return True

    def setFreeFallDuration(self, dur: int) -> bool:
        """
        Set the free-fall detection duration (6-bit value, 1 LSB = 1/ODR).

        :param dur: int, duration 0-63
        :returns: bool, True on success
        """
        self._updateReg(_WAKE_UP_DUR, 0x80, (dur & 0x20) << 2)
        self._updateReg(_FREE_FALL, 0xF8, (dur & 0x1F) << 3)
        return True

    # --- Pedometer ---

    def enablePedometer(self) -> bool:
        """
        Enable the pedometer (sets accel ODR to 26Hz, full scale to 2g).
        Always routed to INT1, matching the Arduino driver.

        :returns: bool, True on success
        """
        self.setAcceleratorOdr(26.0)
        self.setAcceleratorFullScale(2.0)

        self._embUpdateReg(_EMB_FUNC_EN_A, 0x08, 0x00)  # pedo_en = 0 (reset)
        time.sleep_ms(10)

        cur = self._lnPgReadByte(_PEDO_CMD_REG)
        self._lnPgWriteByte(_PEDO_CMD_REG, cur & 0xFA)  # base mode: fp_rejection_en=0, ad_det_en=0

        self._embUpdateReg(_EMB_FUNC_EN_A, 0x08, 0x08)  # pedo_en = 1
        self._embUpdateReg(_EMB_FUNC_INT1, 0x08, 0x08)  # int1_step_detector = 1
        self._updateEmbFuncRoute()
        return True

    def disablePedometer(self) -> bool:
        """
        Disable the pedometer.

        :returns: bool, True on success
        """
        self._embUpdateReg(_EMB_FUNC_INT1, 0x08, 0x00)
        self._embUpdateReg(_EMB_FUNC_EN_A, 0x08, 0x00)
        self._updateEmbFuncRoute()
        return True

    def getStepCounter(self) -> int:
        """
        Read the step counter.

        :returns: int, step count
        """
        self._memBankSet(_BANK_EMBEDDED)
        data = self._readRegs(_STEP_COUNTER_L, 2)
        self._memBankSet(_BANK_USER)
        return struct.unpack("<H", data)[0]

    def resetStepCounter(self) -> bool:
        """
        Reset the step counter.

        :returns: bool, True on success
        """
        self._embUpdateReg(_EMB_FUNC_SRC, 0x80, 0x80)  # pedo_rst_step
        return True

    # --- Tilt detection ---

    def enableTiltDetection(self, int_pin: int = INT1_PIN) -> bool:
        """
        Enable tilt detection (sets accel ODR to 26Hz, full scale to 2g).

        :param int_pin: int, INT1_PIN or INT2_PIN
        :returns: bool, True on success
        """
        self.setAcceleratorOdr(26.0)
        self.setAcceleratorFullScale(2.0)

        self._embUpdateReg(_EMB_FUNC_EN_A, 0x10, 0x00)  # tilt_en = 0 (reset)
        time.sleep_ms(10)
        self._embUpdateReg(_EMB_FUNC_EN_A, 0x10, 0x10)  # tilt_en = 1

        if int_pin == INT1_PIN:
            self._embUpdateReg(_EMB_FUNC_INT1, 0x10, 0x10)
        elif int_pin == INT2_PIN:
            self._embUpdateReg(_EMB_FUNC_INT2, 0x10, 0x10)
        else:
            return False
        self._updateEmbFuncRoute()
        return True

    def disableTiltDetection(self) -> bool:
        """
        Disable tilt detection.

        :returns: bool, True on success
        """
        self._embUpdateReg(_EMB_FUNC_INT1, 0x10, 0x00)
        self._embUpdateReg(_EMB_FUNC_INT2, 0x10, 0x00)
        self._embUpdateReg(_EMB_FUNC_EN_A, 0x10, 0x00)
        self._updateEmbFuncRoute()
        return True

    # --- Wake-up detection ---

    def enableWakeUpDetection(self, int_pin: int = INT1_PIN) -> bool:
        """
        Enable wake-up detection (sets accel ODR to 417Hz, full scale to 2g).

        :param int_pin: int, INT1_PIN or INT2_PIN
        :returns: bool, True on success
        """
        self.setAcceleratorOdr(417.0)
        self.setAcceleratorFullScale(2.0)
        self._updateReg(_WAKE_UP_DUR, 0x60, 0x00)
        self._updateReg(_WAKE_UP_THS, 0x3F, 0x02)

        if int_pin == INT1_PIN:
            self._updateReg(_MD1_CFG, 0x20, 0x20)
        elif int_pin == INT2_PIN:
            self._updateReg(_MD2_CFG, 0x20, 0x20)
        else:
            return False
        self._updateInterruptsEnable()
        return True

    def disableWakeUpDetection(self) -> bool:
        """
        Disable wake-up detection.

        :returns: bool, True on success
        """
        self._updateReg(_MD1_CFG, 0x20, 0x00)
        self._updateReg(_MD2_CFG, 0x20, 0x00)
        self._updateReg(_WAKE_UP_DUR, 0x60, 0x00)
        self._updateReg(_WAKE_UP_THS, 0x3F, 0x00)
        self._updateInterruptsEnable()
        return True

    def setWakeUpThreshold(self, thr: int) -> bool:
        """
        Set the wake-up detection threshold.

        :param thr: int, one of the WAKE_UP_THRESHOLD_* presets
        :returns: bool, True on success
        """
        self._updateReg(_WAKE_UP_THS, 0x3F, thr & 0x3F)
        return True

    def setWakeUpDuration(self, dur: int) -> bool:
        """
        Set the wake-up detection duration.

        :param dur: int, duration 0-3
        :returns: bool, True on success
        """
        self._updateReg(_WAKE_UP_DUR, 0x60, (dur & 0x03) << 5)
        return True

    # --- Tap detection ---

    def enableSingleTapDetection(self, int_pin: int = INT1_PIN) -> bool:
        """
        Enable single-tap detection (sets accel ODR to 417Hz, full scale to 2g).

        :param int_pin: int, INT1_PIN or INT2_PIN
        :returns: bool, True on success
        """
        self.setAcceleratorOdr(417.0)
        self.setAcceleratorFullScale(2.0)
        self._updateReg(_TAP_CFG0, 0x0E, 0x0E)  # TAP_X_EN, TAP_Y_EN, TAP_Z_EN
        self.setTapThreshold(TAP_THRESHOLD_MID_LOW)
        self.setTapShockTime(TAP_SHOCK_TIME_MID_HIGH)
        self.setTapQuietTime(TAP_QUIET_TIME_MID_LOW)

        if int_pin == INT1_PIN:
            self._updateReg(_MD1_CFG, 0x40, 0x40)
        elif int_pin == INT2_PIN:
            self._updateReg(_MD2_CFG, 0x40, 0x40)
        else:
            return False
        self._updateInterruptsEnable()
        return True

    def disableSingleTapDetection(self) -> bool:
        """
        Disable single-tap detection.

        :returns: bool, True on success
        """
        self._updateReg(_MD1_CFG, 0x40, 0x00)
        self._updateReg(_MD2_CFG, 0x40, 0x00)
        self.setTapThreshold(0)
        self.setTapShockTime(0)
        self.setTapQuietTime(0)
        self._updateReg(_TAP_CFG0, 0x0E, 0x00)
        self._updateInterruptsEnable()
        return True

    def enableDoubleTapDetection(self, int_pin: int = INT1_PIN) -> bool:
        """
        Enable double-tap detection (sets accel ODR to 417Hz, full scale to 2g).

        :param int_pin: int, INT1_PIN or INT2_PIN
        :returns: bool, True on success
        """
        self.setAcceleratorOdr(417.0)
        self.setAcceleratorFullScale(2.0)
        self._updateReg(_TAP_CFG0, 0x0E, 0x0E)  # TAP_X_EN, TAP_Y_EN, TAP_Z_EN
        self.setTapThreshold(TAP_THRESHOLD_MID_LOW)
        self.setTapShockTime(TAP_SHOCK_TIME_HIGH)
        self.setTapQuietTime(TAP_QUIET_TIME_HIGH)
        self.setTapDurationTime(TAP_DURATION_TIME_MID)
        self._updateReg(_WAKE_UP_THS, 0x80, 0x80)  # single/double tap = double tap

        if int_pin == INT1_PIN:
            self._updateReg(_MD1_CFG, 0x08, 0x08)
        elif int_pin == INT2_PIN:
            self._updateReg(_MD2_CFG, 0x08, 0x08)
        else:
            return False
        self._updateInterruptsEnable()
        return True

    def disableDoubleTapDetection(self) -> bool:
        """
        Disable double-tap detection.

        :returns: bool, True on success
        """
        self._updateReg(_MD1_CFG, 0x08, 0x00)
        self._updateReg(_MD2_CFG, 0x08, 0x00)
        self.setTapThreshold(0)
        self.setTapShockTime(0)
        self.setTapQuietTime(0)
        self.setTapDurationTime(0)
        self._updateReg(_WAKE_UP_THS, 0x80, 0x00)  # single/double tap = single tap
        self._updateReg(_TAP_CFG0, 0x0E, 0x00)
        self._updateInterruptsEnable()
        return True

    def setTapThreshold(self, thr: int) -> bool:
        """
        Set the tap detection threshold (X axis, used for all tap detection).

        :param thr: int, one of the TAP_THRESHOLD_* presets
        :returns: bool, True on success
        """
        self._updateReg(_TAP_CFG1, 0x1F, thr & 0x1F)
        return True

    def setTapShockTime(self, time_: int) -> bool:
        """
        Set the tap shock time window.

        :param time_: int, one of the TAP_SHOCK_TIME_* presets
        :returns: bool, True on success
        """
        self._updateReg(_INT_DUR2, 0x03, time_ & 0x03)
        return True

    def setTapQuietTime(self, time_: int) -> bool:
        """
        Set the tap quiet time window.

        :param time_: int, one of the TAP_QUIET_TIME_* presets
        :returns: bool, True on success
        """
        self._updateReg(_INT_DUR2, 0x0C, (time_ & 0x03) << 2)
        return True

    def setTapDurationTime(self, time_: int) -> bool:
        """
        Set the tap duration time window.

        :param time_: int, one of the TAP_DURATION_TIME_* presets
        :returns: bool, True on success
        """
        self._updateReg(_INT_DUR2, 0xF0, (time_ & 0x0F) << 4)
        return True

    # --- 6D orientation ---

    def enable6dOrientation(self, int_pin: int = INT1_PIN) -> bool:
        """
        Enable 6D orientation detection (sets accel ODR to 417Hz, full scale to 2g).

        :param int_pin: int, INT1_PIN or INT2_PIN
        :returns: bool, True on success
        """
        self.setAcceleratorOdr(417.0)
        self.setAcceleratorFullScale(2.0)
        self.set6dOrientationThreshold(DEG_60)

        if int_pin == INT1_PIN:
            self._updateReg(_MD1_CFG, 0x04, 0x04)
        elif int_pin == INT2_PIN:
            self._updateReg(_MD2_CFG, 0x04, 0x04)
        else:
            return False
        self._updateInterruptsEnable()
        return True

    def disable6dOrientation(self) -> bool:
        """
        Disable 6D orientation detection.

        :returns: bool, True on success
        """
        self._updateReg(_MD1_CFG, 0x04, 0x00)
        self._updateReg(_MD2_CFG, 0x04, 0x00)
        self.set6dOrientationThreshold(DEG_80)
        self._updateInterruptsEnable()
        return True

    def set6dOrientationThreshold(self, thr: int) -> bool:
        """
        Set the 6D orientation detection threshold.

        :param thr: int, one of the DEG_* presets
        :returns: bool, True on success
        """
        self._updateReg(_TAP_THS_6D, 0x60, (thr & 0x03) << 5)
        return True

    def get6dOrientationXl(self) -> bool:
        """:returns: bool, True if X-low orientation detected"""
        return bool(self._readReg(_D6D_SRC) & 0x01)

    def get6dOrientationXh(self) -> bool:
        """:returns: bool, True if X-high orientation detected"""
        return bool(self._readReg(_D6D_SRC) & 0x02)

    def get6dOrientationYl(self) -> bool:
        """:returns: bool, True if Y-low orientation detected"""
        return bool(self._readReg(_D6D_SRC) & 0x04)

    def get6dOrientationYh(self) -> bool:
        """:returns: bool, True if Y-high orientation detected"""
        return bool(self._readReg(_D6D_SRC) & 0x08)

    def get6dOrientationZl(self) -> bool:
        """:returns: bool, True if Z-low orientation detected"""
        return bool(self._readReg(_D6D_SRC) & 0x10)

    def get6dOrientationZh(self) -> bool:
        """:returns: bool, True if Z-high orientation detected"""
        return bool(self._readReg(_D6D_SRC) & 0x20)

    # --- Event status ---

    def getEventStatus(self) -> dict:
        """
        Read the status of all hardware events.

        :returns: dict with bool keys: freeFall, wakeUp, tap, doubleTap, step, tilt, sixD
        """
        wakeUpSrc = self._readReg(_WAKE_UP_SRC)
        tapSrc = self._readReg(_TAP_SRC)
        d6dSrc = self._readReg(_D6D_SRC)
        md1 = self._readReg(_MD1_CFG)
        md2 = self._readReg(_MD2_CFG)

        self._memBankSet(_BANK_EMBEDDED)
        try:
            embInt1 = self._readReg(_EMB_FUNC_INT1)
            embInt2 = self._readReg(_EMB_FUNC_INT2)
            embSrc = self._readReg(_EMB_FUNC_SRC)
            embStatus = self._readReg(_EMB_FUNC_STATUS)
        finally:
            self._memBankSet(_BANK_USER)

        status = {
            "freeFall": False,
            "wakeUp": False,
            "tap": False,
            "doubleTap": False,
            "step": False,
            "tilt": False,
            "sixD": False,
        }

        if (md1 & 0x10) or (md2 & 0x10):
            status["freeFall"] = bool(wakeUpSrc & 0x20)

        if (md1 & 0x20) or (md2 & 0x20):
            status["wakeUp"] = bool(wakeUpSrc & 0x08)

        if (md1 & 0x40) or (md2 & 0x40):
            status["tap"] = bool(tapSrc & 0x20)

        if (md1 & 0x08) or (md2 & 0x08):
            status["doubleTap"] = bool(tapSrc & 0x10)

        if (md1 & 0x04) or (md2 & 0x04):
            status["sixD"] = bool(d6dSrc & 0x40)

        if embInt1 & 0x08:
            status["step"] = bool(embSrc & 0x20)

        if (embInt1 & 0x10) or (embInt2 & 0x10):
            status["tilt"] = bool(embStatus & 0x10)

        return status

    # --- Interrupt master-enable gating ---
    # MD1_CFG/MD2_CFG only route a source to a pin; TAP_CFG2.interrupts_enable
    # is a separate master gate that must also be set for free-fall, wake-up,
    # 6D orientation and tap/double-tap to actually reach the pin. Likewise,
    # MD1_CFG.int1_emb_func/MD2_CFG.int2_emb_func gate embedded-function
    # sources (pedometer step detector, tilt) routed via EMB_FUNC_INT1/INT2.
    # Both must be recomputed after every route change since disabling one
    # source must not turn off the gate while another source is still active.

    def _updateInterruptsEnable(self):
        md1 = self._readReg(_MD1_CFG)
        md2 = self._readReg(_MD2_CFG)
        basicMask = 0x04 | 0x08 | 0x10 | 0x20 | 0x40  # 6d, doubleTap, freeFall, wakeUp, singleTap
        self._updateReg(_TAP_CFG2, 0x80, 0x80 if (md1 & basicMask) or (md2 & basicMask) else 0x00)

    def _updateEmbFuncRoute(self):
        embInt1 = self._embReadReg(_EMB_FUNC_INT1)
        embInt2 = self._embReadReg(_EMB_FUNC_INT2)
        embMask = 0x08 | 0x10  # step_detector, tilt
        self._updateReg(_MD1_CFG, 0x02, 0x02 if embInt1 & embMask else 0x00)
        self._updateReg(_MD2_CFG, 0x02, 0x02 if embInt2 & embMask else 0x00)

    # --- Raw register access ---

    def readRegister(self, reg: int) -> int:
        """
        Read a raw register (user bank).

        :param reg: int, register address
        :returns: int, register value
        """
        return self._readReg(reg)

    def writeRegister(self, reg: int, data: int) -> bool:
        """
        Write a raw register (user bank).

        :param reg: int, register address
        :param data: int, value to write
        :returns: bool, True on success
        """
        self._writeReg(reg, data)
        return True

    # --- Low-level I2C ---

    def _readReg(self, reg):
        try:
            return self.i2c.readfrom_mem(self.address, reg, 1)[0]
        except OSError as e:
            raise Exception("I2C read error: {}".format(e))

    def _readRegs(self, reg, length):
        try:
            return self.i2c.readfrom_mem(self.address, reg, length)
        except OSError as e:
            raise Exception("I2C read error: {}".format(e))

    def _writeReg(self, reg, value):
        try:
            self.i2c.writeto_mem(self.address, reg, bytes([value & 0xFF]))
        except OSError as e:
            raise Exception("I2C write error: {}".format(e))

    def _updateReg(self, reg, mask, value):
        cur = self._readReg(reg)
        new = (cur & (~mask & 0xFF)) | (value & mask)
        self._writeReg(reg, new)

    # --- Embedded-function bank access ---
    # Pedometer/tilt enables and their interrupt routing, the step counter and
    # the pedometer command register all live behind FUNC_CFG_ACCESS, in a
    # separate register bank that reuses the same numeric addresses as the
    # user bank. Every access here switches in, does the operation, and
    # switches back to the user bank before returning.

    def _memBankSet(self, bank):
        self._writeReg(_FUNC_CFG_ACCESS, bank)

    def _embReadReg(self, reg):
        self._memBankSet(_BANK_EMBEDDED)
        try:
            return self._readReg(reg)
        finally:
            self._memBankSet(_BANK_USER)

    def _embUpdateReg(self, reg, mask, value):
        self._memBankSet(_BANK_EMBEDDED)
        try:
            self._updateReg(reg, mask, value)
        finally:
            self._memBankSet(_BANK_USER)

    def _lnPgReadByte(self, address):
        self._memBankSet(_BANK_EMBEDDED)
        try:
            self._updateReg(_PAGE_RW, 0x60, 0x20)  # page_read enable
            self._writeReg(_PAGE_SEL, (((address >> 8) & 0x0F) << 4) | 0x01)
            self._writeReg(_PAGE_ADDRESS, address & 0xFF)
            val = self._readReg(_PAGE_VALUE)
            self._updateReg(_PAGE_RW, 0x60, 0x00)  # disable
            return val
        finally:
            self._memBankSet(_BANK_USER)

    def _lnPgWriteByte(self, address, value):
        self._memBankSet(_BANK_EMBEDDED)
        try:
            self._updateReg(_PAGE_RW, 0x60, 0x40)  # page_write enable
            self._writeReg(_PAGE_SEL, (((address >> 8) & 0x0F) << 4) | 0x01)
            self._writeReg(_PAGE_ADDRESS, address & 0xFF)
            self._writeReg(_PAGE_VALUE, value & 0xFF)
            self._updateReg(_PAGE_RW, 0x60, 0x00)  # disable
        finally:
            self._memBankSet(_BANK_USER)
