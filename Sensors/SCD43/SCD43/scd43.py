# FILE: scd43.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython library for the SCD43 CO2 Sensor
# LAST UPDATED: 2026-05-20
import time
from machine import I2C

_I2C_ADDR = 0x62

_CMD_START_PERIODIC   = 0x21B1
_CMD_READ_MEAS        = 0xEC05
_CMD_STOP_PERIODIC    = 0x3F86
_CMD_SET_TEMP_OFFSET  = 0x241D
_CMD_GET_TEMP_OFFSET  = 0x2318
_CMD_SET_ALTITUDE     = 0x2427
_CMD_GET_ALTITUDE     = 0x2322
_CMD_SET_PRESSURE     = 0xE000
_CMD_SET_ASC_ENABLED  = 0x2416
_CMD_GET_ASC_ENABLED  = 0x2313
_CMD_SET_ASC_TARGET   = 0x243A
_CMD_GET_ASC_TARGET   = 0x233F
_CMD_START_LP_PERIODIC = 0x21AC
_CMD_DATA_READY       = 0xE4B8
_CMD_PERSIST          = 0x3615
_CMD_SERIAL_NUMBER    = 0x3682
_CMD_SELF_TEST        = 0x3639
_CMD_FACTORY_RESET    = 0x3632
_CMD_REINIT           = 0x3646
_CMD_SENSOR_VARIANT   = 0x202F
_CMD_SINGLE_SHOT      = 0x219D
_CMD_SINGLE_SHOT_RHT  = 0x2196
_CMD_POWER_DOWN       = 0x36E0
_CMD_WAKE_UP          = 0x36F6

VARIANT_SCD40 = 0x0000
VARIANT_SCD41 = 0x1000
VARIANT_SCD42 = 0x2000
VARIANT_SCD43 = 0x5000
VARIANT_UNKNOWN = 0xF000


def _crc8(data):
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


class SCD43:
    def __init__(self):
        self._i2c = None
        self._co2 = 0
        self._temperature = 0.0
        self._humidity = 0.0

    def begin(self, i2c):
        self._i2c = i2c
        # Stop any in-progress measurement (error ignored — sensor may be idle)
        try:
            self._sendCmd(_CMD_STOP_PERIODIC)
            time.sleep_ms(500)
        except OSError:
            pass
        # Verify communication by reading serial number
        try:
            self._sendCmd(_CMD_SERIAL_NUMBER)
            time.sleep_ms(1)
            self._readWords(3)
        except OSError:
            return False
        return self.startPeriodicMeasurement()

    # -------------------------------------------------------------------------
    # Measurement control
    # -------------------------------------------------------------------------

    def startPeriodicMeasurement(self):
        try:
            self._sendCmd(_CMD_START_PERIODIC)
            return True
        except OSError:
            return False

    def stopPeriodicMeasurement(self):
        try:
            self._sendCmd(_CMD_STOP_PERIODIC)
            time.sleep_ms(500)
            return True
        except OSError:
            return False

    def startLowPowerPeriodicMeasurement(self):
        try:
            self._sendCmd(_CMD_START_LP_PERIODIC)
            return True
        except OSError:
            return False

    # -------------------------------------------------------------------------
    # Data acquisition
    # -------------------------------------------------------------------------

    def readMeasurement(self):
        if not self.getDataReadyStatus():
            return False
        try:
            self._sendCmd(_CMD_READ_MEAS)
            time.sleep_ms(1)
            words = self._readWords(3)
        except OSError:
            return False
        self._co2 = words[0]
        self._temperature = -45.0 + (175.0 * words[1] / 65535.0)
        self._humidity = 100.0 * words[2] / 65535.0
        return True

    def getDataReadyStatus(self):
        try:
            self._sendCmd(_CMD_DATA_READY)
            time.sleep_ms(1)
            words = self._readWords(1)
        except OSError:
            return False
        return (words[0] & 0x07FF) != 0

    # -------------------------------------------------------------------------
    # Measurement getters
    # -------------------------------------------------------------------------

    def getCO2(self):
        return self._co2

    def getTemperature(self):
        return self._temperature

    def getHumidity(self):
        return self._humidity

    # -------------------------------------------------------------------------
    # Signal compensation
    # -------------------------------------------------------------------------

    def setTemperatureOffset(self, offsetCelsius):
        raw = int(round(offsetCelsius * 65535.0 / 175.0))
        raw = max(0, min(0xFFFF, raw))
        try:
            self._sendCmdWithWord(_CMD_SET_TEMP_OFFSET, raw)
            time.sleep_ms(1)
            return True
        except OSError:
            return False

    def getTemperatureOffset(self):
        try:
            self._sendCmd(_CMD_GET_TEMP_OFFSET)
            time.sleep_ms(1)
            words = self._readWords(1)
        except OSError:
            return 0.0
        return 175.0 * words[0] / 65535.0

    def setSensorAltitude(self, altitudeMeters):
        try:
            self._sendCmdWithWord(_CMD_SET_ALTITUDE, altitudeMeters)
            time.sleep_ms(1)
            return True
        except OSError:
            return False

    def getSensorAltitude(self):
        try:
            self._sendCmd(_CMD_GET_ALTITUDE)
            time.sleep_ms(1)
            words = self._readWords(1)
        except OSError:
            return 0
        return words[0]

    def setAmbientPressure(self, pressurePa):
        raw = int(round(pressurePa / 100.0))
        raw = max(0, min(0xFFFF, raw))
        try:
            self._sendCmdWithWord(_CMD_SET_PRESSURE, raw)
            time.sleep_ms(1)
            return True
        except OSError:
            return False

    # -------------------------------------------------------------------------
    # Automatic self-calibration (ASC)
    # -------------------------------------------------------------------------

    def setAutomaticSelfCalibrationEnabled(self, enabled):
        try:
            self._sendCmdWithWord(_CMD_SET_ASC_ENABLED, 1 if enabled else 0)
            time.sleep_ms(1)
            return True
        except OSError:
            return False

    def getAutomaticSelfCalibrationEnabled(self):
        try:
            self._sendCmd(_CMD_GET_ASC_ENABLED)
            time.sleep_ms(1)
            words = self._readWords(1)
        except OSError:
            return False
        return words[0] != 0

    def setAutomaticSelfCalibrationTarget(self, targetPpm):
        try:
            self._sendCmdWithWord(_CMD_SET_ASC_TARGET, targetPpm)
            time.sleep_ms(1)
            return True
        except OSError:
            return False

    def getAutomaticSelfCalibrationTarget(self):
        try:
            self._sendCmd(_CMD_GET_ASC_TARGET)
            time.sleep_ms(1)
            words = self._readWords(1)
        except OSError:
            return 0
        return words[0]

    # -------------------------------------------------------------------------
    # Configuration persistence
    # -------------------------------------------------------------------------

    def persistSettings(self):
        try:
            self._sendCmd(_CMD_PERSIST)
            time.sleep_ms(800)
            return True
        except OSError:
            return False

    # -------------------------------------------------------------------------
    # Device information
    # -------------------------------------------------------------------------

    def getSerialNumber(self):
        try:
            self._sendCmd(_CMD_SERIAL_NUMBER)
            time.sleep_ms(1)
            words = self._readWords(3)
        except OSError:
            return None
        return (words[0] << 32) | (words[1] << 16) | words[2]

    # -------------------------------------------------------------------------
    # Self-test and maintenance
    # -------------------------------------------------------------------------

    def performSelfTest(self):
        try:
            self._sendCmd(_CMD_SELF_TEST)
            time.sleep_ms(10000)
            words = self._readWords(1)
        except OSError:
            return False
        return words[0] == 0

    def performFactoryReset(self):
        try:
            self._sendCmd(_CMD_FACTORY_RESET)
            time.sleep_ms(1200)
            return True
        except OSError:
            return False

    def reinit(self):
        try:
            self._sendCmd(_CMD_REINIT)
            time.sleep_ms(30)
            return True
        except OSError:
            return False

    # -------------------------------------------------------------------------
    # Single-shot mode (SCD43)
    # -------------------------------------------------------------------------

    def measureSingleShot(self):
        try:
            self._sendCmd(_CMD_SINGLE_SHOT)
            time.sleep_ms(5000)
            return True
        except OSError:
            return False

    def measureSingleShotRhtOnly(self):
        try:
            self._sendCmd(_CMD_SINGLE_SHOT_RHT)
            time.sleep_ms(50)
            return True
        except OSError:
            return False

    def measureAndReadSingleShot(self):
        if not self.measureSingleShot():
            return False
        while not self.getDataReadyStatus():
            time.sleep_ms(100)
        return self.readMeasurement()

    def powerDown(self):
        try:
            self._sendCmd(_CMD_POWER_DOWN)
            time.sleep_ms(1)
            return True
        except OSError:
            return False

    def wakeUp(self):
        # Sensor does not ACK this command — suppress the OSError
        try:
            self._sendCmd(_CMD_WAKE_UP)
        except OSError:
            pass
        time.sleep_ms(30)
        return True

    # -------------------------------------------------------------------------
    # Sensor variant
    # -------------------------------------------------------------------------

    def getSensorVariant(self):
        try:
            self._sendCmd(_CMD_SENSOR_VARIANT)
            time.sleep_ms(1)
            words = self._readWords(1)
        except OSError:
            return VARIANT_UNKNOWN
        masked = words[0] & 0xF000
        if masked == VARIANT_SCD40:
            return VARIANT_SCD40
        elif masked == VARIANT_SCD41:
            return VARIANT_SCD41
        elif masked == VARIANT_SCD42:
            return VARIANT_SCD42
        elif masked == VARIANT_SCD43:
            return VARIANT_SCD43
        return VARIANT_UNKNOWN

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _sendCmd(self, cmd):
        self._i2c.writeto(_I2C_ADDR, bytes([cmd >> 8, cmd & 0xFF]))

    def _sendCmdWithWord(self, cmd, word):
        hi = (word >> 8) & 0xFF
        lo = word & 0xFF
        crc = _crc8([hi, lo])
        self._i2c.writeto(_I2C_ADDR, bytes([cmd >> 8, cmd & 0xFF, hi, lo, crc]))

    def _readWords(self, count):
        data = self._i2c.readfrom(_I2C_ADDR, count * 3)
        words = []
        for i in range(count):
            hi = data[i * 3]
            lo = data[i * 3 + 1]
            crc = data[i * 3 + 2]
            if _crc8([hi, lo]) != crc:
                raise OSError("CRC mismatch")
            words.append((hi << 8) | lo)
        return words
