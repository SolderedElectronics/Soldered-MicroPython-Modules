# FILE: iis2dulpx.py
# AUTHOR: Josip Simun Kuci @ Soldered
# BRIEF: MicroPython library for the IIS2DULPX 3-axis accelerometer
# LAST UPDATED: 2026-04-24

import time
from machine import I2C, Pin
from os import uname

IIS2DULPX_OK = 0
IIS2DULPX_ERROR = -1

IIS2DULPX_INT1_PIN = 0
IIS2DULPX_INT2_PIN = 1

IIS2DULPX_ULTRA_LOW_POWER = 0
IIS2DULPX_LOW_POWER = 1
IIS2DULPX_HIGH_PERFORMANCE = 2

_IIS2DULPX_I2C_ADDR_L = 0x18
_IIS2DULPX_I2C_ADDR_H = 0x19
_IIS2DULPX_ID = 0x47

_REG_WAKE_UP_DUR_EXT = 0x0E
_REG_WHO_AM_I = 0x0F
_REG_CTRL1 = 0x10
_REG_CTRL3 = 0x12
_REG_CTRL4 = 0x13
_REG_CTRL5 = 0x14
_REG_I3C_IF_CTRL = 0x33
_REG_FUNC_CFG_ACCESS = 0x3F
_REG_INTERRUPT_CFG = 0x17
_REG_WAKE_UP_THS = 0x1C
_REG_WAKE_UP_DUR = 0x1D
_REG_MD1_CFG = 0x1F
_REG_MD2_CFG = 0x20
_REG_ALL_INT_SRC = 0x24
_REG_STATUS = 0x25
_REG_OUT_X_L = 0x28

_ACC_SENS_MG_LSB = {
    2: 0.061,
    4: 0.122,
    8: 0.244,
    16: 0.488,
}

_FS_TO_BITS = {
    2: 0b00,
    4: 0b01,
    8: 0b10,
    16: 0b11,
}

_BITS_TO_FS = {
    0b00: 2,
    0b01: 4,
    0b10: 8,
    0b11: 16,
}

# CTRL5 ODR field (matches iis2dulpx_mode_get in ST driver), not sequential 0..N
_BITS_TO_ODR = {
    0x0: 0.0,
    0x1: 1.6,
    0x2: 3.0,
    0x3: 25.0,
    0x4: 6.0,
    0x5: 12.5,
    0x6: 25.0,
    0x7: 50.0,
    0x8: 100.0,
    0x9: 200.0,
    0xA: 400.0,
    0xB: 800.0,
}


class IIS2DULPX:
    def __init__(self, i2c=None, address=_IIS2DULPX_I2C_ADDR_H):
        if i2c is not None:
            self.i2c = i2c
        else:
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, enter I2C pins manually")

        self.address = address
        self._acc_is_enabled = False
        self._is_initialized = False
        self._acc_odr = 100.0
        self._power_mode = IIS2DULPX_HIGH_PERFORMANCE

    def begin(self):
        if self.ReadID() != _IIS2DULPX_ID:
            return IIS2DULPX_ERROR

        # Boot / interface wake-up (matches STM IIS2DULPXSensor::begin())
        time.sleep_ms(25)

        # Prefer I2C behaviour on the serial bus (ASF / I3C ctrl — same as Arduino driver)
        i3c = self._read_reg(_REG_I3C_IF_CTRL)
        self._write_reg(_REG_I3C_IF_CTRL, i3c | (1 << 5))

        # Accelerometer data lives in the main register bank; embedded bank reads as zeros here
        self._write_reg(_REG_FUNC_CFG_ACCESS, self._read_reg(_REG_FUNC_CFG_ACCESS) & 0x7F)

        # BDU + no embedded funcs + address auto-increment (iis2dulpx_init_set SENSOR_ONLY_ON)
        ctrl4 = self._read_reg(_REG_CTRL4)
        ctrl4 &= ~(1 << 4)
        ctrl4 |= 1 << 5
        self._write_reg(_REG_CTRL4, ctrl4)

        ctrl1 = self._read_reg(_REG_CTRL1)
        self._write_reg(_REG_CTRL1, ctrl1 | (1 << 4))

        # Default: powered down, FS = 2g
        self._set_ctrl5(fs=2, odr=0.0)
        self._is_initialized = True
        self._acc_is_enabled = False
        return IIS2DULPX_OK

    def end(self):
        self.Disable_X()
        self._is_initialized = False
        self._acc_odr = 0.0
        self._power_mode = IIS2DULPX_LOW_POWER
        return IIS2DULPX_OK

    def ReadID(self):
        return self._read_reg(_REG_WHO_AM_I)

    def Enable_X(self):
        if self._acc_is_enabled:
            return IIS2DULPX_OK
        status = self.Set_X_OutputDataRate_With_Mode(self._acc_odr, self._power_mode)
        if status != IIS2DULPX_OK:
            return status
        # Must apply ODR here: Set_X_OutputDataRate_With_Mode skips HW while disabled
        self._set_ctrl5(odr=self._acc_odr)
        self._acc_is_enabled = True
        return IIS2DULPX_OK

    def Disable_X(self):
        self._set_ctrl5(odr=0.0)
        self._acc_is_enabled = False
        return IIS2DULPX_OK

    def Get_X_Sensitivity(self):
        full_scale = self.Get_X_FullScale()
        return _ACC_SENS_MG_LSB.get(full_scale, -1.0)

    def Get_X_OutputDataRate(self):
        ctrl5 = self._read_reg(_REG_CTRL5)
        odr_bits = (ctrl5 >> 4) & 0x0F
        return _BITS_TO_ODR.get(odr_bits, -1.0)

    def Set_X_OutputDataRate(self, odr):
        return self.Set_X_OutputDataRate_With_Mode(odr, IIS2DULPX_HIGH_PERFORMANCE)

    def Set_X_OutputDataRate_With_Mode(self, odr, power_mode):
        selected_odr = self._select_odr(odr, power_mode)
        if selected_odr is None:
            return IIS2DULPX_ERROR

        self._power_mode = power_mode
        self._acc_odr = selected_odr
        if self._acc_is_enabled:
            self._set_ctrl5(odr=selected_odr)
        return IIS2DULPX_OK

    def Get_X_FullScale(self):
        ctrl5 = self._read_reg(_REG_CTRL5)
        fs_bits = ctrl5 & 0x03
        return _BITS_TO_FS.get(fs_bits, -1)

    def Set_X_FullScale(self, full_scale):
        if full_scale <= 2:
            fs = 2
        elif full_scale <= 4:
            fs = 4
        elif full_scale <= 8:
            fs = 8
        else:
            fs = 16
        self._set_ctrl5(fs=fs)
        return IIS2DULPX_OK

    def Get_X_AxesRaw(self):
        data = self.i2c.readfrom_mem(self.address, _REG_OUT_X_L, 6)
        x = self._to_int16(data[0], data[1])
        y = self._to_int16(data[2], data[3])
        z = self._to_int16(data[4], data[5])
        return x, y, z

    def Get_X_Axes(self):
        x_raw, y_raw, z_raw = self.Get_X_AxesRaw()
        sens = self.Get_X_Sensitivity()
        if sens <= 0:
            return 0, 0, 0
        x = int(x_raw * sens)
        y = int(y_raw * sens)
        z = int(z_raw * sens)
        return x, y, z

    def Read_Reg(self, reg):
        return self._read_reg(reg)

    def Write_Reg(self, reg, data):
        self._write_reg(reg, data)
        return IIS2DULPX_OK

    def Get_X_DRDY_Status(self):
        status = self._read_reg(_REG_STATUS)
        return 1 if (status & 0x01) else 0

    def Get_X_Init_Status(self):
        return 1 if self._is_initialized else 0

    def Get_X_Event_Status(self):
        all_int_src = self._read_reg(_REG_ALL_INT_SRC)
        md1_cfg = self._read_reg(_REG_MD1_CFG)
        md2_cfg = self._read_reg(_REG_MD2_CFG)

        wakeup_enabled = ((md1_cfg >> 5) & 0x01) or ((md2_cfg >> 5) & 0x01)
        sixd_enabled = ((md1_cfg >> 2) & 0x01) or ((md2_cfg >> 2) & 0x01)

        return {
            "FreeFallStatus": 0,
            "TapStatus": 0,
            "DoubleTapStatus": 0,
            "WakeUpStatus": 1 if (wakeup_enabled and ((all_int_src >> 1) & 0x01)) else 0,
            "StepStatus": 0,
            "TiltStatus": 0,
            "D6DOrientationStatus": 1 if (sixd_enabled and ((all_int_src >> 5) & 0x01)) else 0,
            "SleepStatus": 0,
        }

    def Enable_Wake_Up_Detection(self, int_pin=IIS2DULPX_INT1_PIN):
        if self.Set_X_OutputDataRate(200.0) != IIS2DULPX_OK:
            return IIS2DULPX_ERROR
        if self.Set_X_FullScale(2) != IIS2DULPX_OK:
            return IIS2DULPX_ERROR
        if self.Set_Wake_Up_Threshold(63) != IIS2DULPX_OK:
            return IIS2DULPX_ERROR
        if self.Set_Wake_Up_Duration(0) != IIS2DULPX_OK:
            return IIS2DULPX_ERROR

        ctrl1 = self._read_reg(_REG_CTRL1)
        ctrl1 |= 0x07  # Enable wake-up on X, Y, Z
        self._write_reg(_REG_CTRL1, ctrl1)

        if int_pin == IIS2DULPX_INT1_PIN:
            md1 = self._read_reg(_REG_MD1_CFG)
            self._write_reg(_REG_MD1_CFG, md1 | (1 << 5))
        elif int_pin == IIS2DULPX_INT2_PIN:
            md2 = self._read_reg(_REG_MD2_CFG)
            self._write_reg(_REG_MD2_CFG, md2 | (1 << 5))
        else:
            return IIS2DULPX_ERROR

        interrupt_cfg = self._read_reg(_REG_INTERRUPT_CFG)
        self._write_reg(_REG_INTERRUPT_CFG, interrupt_cfg | 0x01)
        return IIS2DULPX_OK

    def Disable_Wake_Up_Detection(self):
        md1 = self._read_reg(_REG_MD1_CFG)
        md2 = self._read_reg(_REG_MD2_CFG)
        ctrl1 = self._read_reg(_REG_CTRL1)

        self._write_reg(_REG_MD1_CFG, md1 & ~(1 << 5))
        self._write_reg(_REG_MD2_CFG, md2 & ~(1 << 5))
        self._write_reg(_REG_CTRL1, ctrl1 & ~0x07)
        self.Set_Wake_Up_Threshold(0)
        self.Set_Wake_Up_Duration(0)
        return IIS2DULPX_OK

    def Set_Wake_Up_Threshold(self, threshold_mg):
        fs = self.Get_X_FullScale()
        if fs not in (2, 4, 8, 16):
            return IIS2DULPX_ERROR

        if fs == 2:
            small_step, large_step = 7.8125, 31.25
        elif fs == 4:
            small_step, large_step = 15.625, 62.5
        elif fs == 8:
            small_step, large_step = 31.25, 125.0
        else:
            small_step, large_step = 62.5, 250.0

        interrupt_cfg = self._read_reg(_REG_INTERRUPT_CFG)
        if threshold_mg < small_step * 63.0:
            interrupt_cfg |= (1 << 5)
            wk_ths = int(threshold_mg / small_step)
        elif threshold_mg < large_step * 63.0:
            interrupt_cfg &= ~(1 << 5)
            wk_ths = int(threshold_mg / large_step)
        else:
            interrupt_cfg &= ~(1 << 5)
            wk_ths = 63

        self._write_reg(_REG_INTERRUPT_CFG, interrupt_cfg)

        wake_up_ths = self._read_reg(_REG_WAKE_UP_THS)
        wake_up_ths = (wake_up_ths & 0xC0) | (wk_ths & 0x3F)
        self._write_reg(_REG_WAKE_UP_THS, wake_up_ths)
        return IIS2DULPX_OK

    def Set_Wake_Up_Duration(self, duration):
        if duration not in (0, 1, 2, 3, 7, 11, 15):
            return IIS2DULPX_ERROR

        wake_up_dur = self._read_reg(_REG_WAKE_UP_DUR)
        dur_ext = self._read_reg(_REG_WAKE_UP_DUR_EXT)

        if duration in (0, 1, 2):
            dur_ext &= ~(1 << 4)
            wake_dur_bits = duration
        else:
            dur_ext |= (1 << 4)
            wake_dur_bits = {3: 0, 7: 1, 11: 2, 15: 3}[duration]

        wake_up_dur = (wake_up_dur & ~(0b11 << 5)) | ((wake_dur_bits & 0b11) << 5)
        self._write_reg(_REG_WAKE_UP_DUR, wake_up_dur)
        self._write_reg(_REG_WAKE_UP_DUR_EXT, dur_ext)
        return IIS2DULPX_OK

    def _select_odr(self, odr, power_mode):
        if power_mode == IIS2DULPX_ULTRA_LOW_POWER:
            if odr <= 1.6:
                return 1.6
            if odr <= 3.0:
                return 3.0
            return 25.0
        if power_mode in (IIS2DULPX_LOW_POWER, IIS2DULPX_HIGH_PERFORMANCE):
            for odr_val in (6.0, 12.5, 25.0, 50.0, 100.0, 200.0, 400.0, 800.0):
                if odr <= odr_val:
                    return odr_val
            return 800.0
        return None

    def _odr_float_to_nibble(self, rate, power_mode):
        if power_mode == IIS2DULPX_ULTRA_LOW_POWER:
            if rate <= 1.6:
                return 0x1
            if rate <= 3.0:
                return 0x2
            return 0x3
        if rate <= 6.0:
            return 0x4
        if rate <= 12.5:
            return 0x5
        if rate <= 25.0:
            return 0x6
        if rate <= 50.0:
            return 0x7
        if rate <= 100.0:
            return 0x8
        if rate <= 200.0:
            return 0x9
        if rate <= 400.0:
            return 0xA
        return 0xB

    def _set_ctrl5(self, fs=None, odr=None):
        ctrl5 = self._read_reg(_REG_CTRL5)
        ctrl3 = self._read_reg(_REG_CTRL3)
        if fs is not None:
            ctrl5 = (ctrl5 & 0xFC) | _FS_TO_BITS[fs]
        if odr is not None:
            if odr == 0.0:
                ctrl5 = ctrl5 & 0x0F
                ctrl3 &= ~(1 << 2)
            else:
                nib = self._odr_float_to_nibble(odr, self._power_mode)
                ctrl5 = (ctrl5 & 0x0F) | ((nib & 0x0F) << 4)
                if self._power_mode == IIS2DULPX_HIGH_PERFORMANCE:
                    ctrl3 |= 1 << 2
                else:
                    ctrl3 &= ~(1 << 2)
            self._write_reg(_REG_CTRL3, ctrl3)
        self._write_reg(_REG_CTRL5, ctrl5)

    def _read_reg(self, reg):
        return self.i2c.readfrom_mem(self.address, reg, 1)[0]

    def _write_reg(self, reg, value):
        self.i2c.writeto_mem(self.address, reg, bytes([value & 0xFF]))

    @staticmethod
    def _to_int16(lsb, msb):
        value = (msb << 8) | lsb
        if value & 0x8000:
            value -= 0x10000
        return value
