# FILE: ElectrochemicalGasSensor.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython library for the Soldered Electrochemical Gas Sensor breakout (ADS1115 + LMP91000)
# LAST UPDATED: 2026-05-21

from machine import I2C, Pin
from os import uname
import time

from ads1115 import ADS1115, ADS_GAIN_6_144V, ADS_GAIN_4_096V, ADS_GAIN_2_048V
from lmp91000 import LMP91000

# ===========================================================================
# Board constants
# ===========================================================================
_DEFAULT_ADC_ADDR = 0x49
_REF_VOLTAGE      = 2.5  # External reference voltage on board (V)

# ===========================================================================
# ATtiny bridge protocol constants - keep in sync with
# extras/attiny_firmware/BridgeProtocol.h (separate toolchains, can't share one file)
# ===========================================================================
_CMD_PING          = 0x01
_CMD_CONFIGURE_ADC = 0x02
_CMD_CONFIGURE_LMP = 0x03
_CMD_TRIGGER_ADC   = 0x04

_BRIDGE_STATUS_BUSY  = 0x00
_BRIDGE_STATUS_OK    = 0x01
_BRIDGE_STATUS_ERROR = 0x02
_BRIDGE_STATUS_NONE  = 0xFF

# Bridge boards (ATtiny, easyC jumpers) use 0x30-0x37; legacy direct-wired boards
# use the ADS1115's own address range (0x48-0x4B) - begin() dispatches on this.
_BRIDGE_ADDR_MIN   = 0x30
_BRIDGE_ADDR_MAX   = 0x37
_BRIDGE_TIMEOUT_MS = 500

# ===========================================================================
# LMP91000 TIA gain config values
# ===========================================================================
TIA_GAIN_EXTERNAL  = 0x00
TIA_GAIN_2_75_KOHM = 0x01
TIA_GAIN_3_5_KOHM  = 0x02
TIA_GAIN_7_KOHM    = 0x03
TIA_GAIN_14_KOHM   = 0x04
TIA_GAIN_35_KOHM   = 0x05
TIA_GAIN_120_KOHM  = 0x06
TIA_GAIN_350_KOHM  = 0x07

# RLOAD
RLOAD_10_OHM  = 0x00
RLOAD_33_OHM  = 0x01
RLOAD_50_OHM  = 0x02
RLOAD_100_OHM = 0x03

# Reference source
REF_INTERNAL = 0x00
REF_EXTERNAL = 0x01

# Internal zero
INTERNAL_ZERO_20_PERCENT = 0x00
INTERNAL_ZERO_50_PERCENT = 0x01
INTERNAL_ZERO_67_PERCENT = 0x02
INTERNAL_ZERO_BYPASSED   = 0x03

# Bias sign
BIAS_SIGN_NEGATIVE = 0x00
BIAS_SIGN_POSITIVE = 0x01

# Bias percentage
BIAS_0_PERCENT  = 0x00
BIAS_1_PERCENT  = 0x01
BIAS_2_PERCENT  = 0x02
BIAS_4_PERCENT  = 0x03
BIAS_6_PERCENT  = 0x04
BIAS_8_PERCENT  = 0x05
BIAS_10_PERCENT = 0x06
BIAS_12_PERCENT = 0x07
BIAS_14_PERCENT = 0x08
BIAS_16_PERCENT = 0x09
BIAS_18_PERCENT = 0x0A
BIAS_20_PERCENT = 0x0B
BIAS_22_PERCENT = 0x0C
BIAS_24_PERCENT = 0x0D

# FET short
FET_SHORT_DISABLED = 0x00
FET_SHORT_ENABLED  = 0x01

# Operation mode
OP_MODE_DEEP_SLEEP          = 0x00
OP_MODE_2LEAD_GROUND_CELL   = 0x01
OP_MODE_STANDBY             = 0x02
OP_MODE_3LEAD_AMP_CELL      = 0x03
OP_MODE_TEMPERATURE_TIA_OFF = 0x06
OP_MODE_TEMPERATURE_TIA_ON  = 0x07

# ===========================================================================
# Lookup tables
# ===========================================================================
_TIA_GAIN_TABLE = {
    TIA_GAIN_EXTERNAL:  -1,
    TIA_GAIN_2_75_KOHM: 2750.0,
    TIA_GAIN_3_5_KOHM:  3500.0,
    TIA_GAIN_7_KOHM:    7000.0,
    TIA_GAIN_14_KOHM:   14000.0,
    TIA_GAIN_35_KOHM:   35000.0,
    TIA_GAIN_120_KOHM:  120000.0,
    TIA_GAIN_350_KOHM:  350000.0,
}

_INTERNAL_ZERO_TABLE = {
    INTERNAL_ZERO_20_PERCENT: 20.0,
    INTERNAL_ZERO_50_PERCENT: 50.0,
    INTERNAL_ZERO_67_PERCENT: 67.0,
    INTERNAL_ZERO_BYPASSED:   -1,
}


# ===========================================================================
# Sensor configuration class
# ===========================================================================
class SensorConfig:
    """Holds configuration parameters for a specific electrochemical gas sensor."""

    def __init__(self, nano_amperes_per_ppm, internal_zero_calibration, ads_gain,
                 tia_gain, rload, ref_source, internal_zero, bias_sign, bias,
                 fet_short, op_mode):
        self.nanoAmperesPerPPM       = nano_amperes_per_ppm
        self.internalZeroCalibration = internal_zero_calibration
        self.adsGain                 = ads_gain
        self.TIA_GAIN_IN_KOHMS       = tia_gain
        self.RLOAD                   = rload
        self.REF_SOURCE              = ref_source
        self.INTERNAL_ZERO           = internal_zero
        self.BIAS_SIGN               = bias_sign
        self.BIAS                    = bias
        self.FET_SHORT               = fet_short
        self.OP_MODE                 = op_mode


# ===========================================================================
# Predefined sensor configurations
# ===========================================================================

# SGX-4CO — Carbon Monoxide
SENSOR_CO = SensorConfig(
    nano_amperes_per_ppm=70.0,
    internal_zero_calibration=0,
    ads_gain=ADS_GAIN_4_096V,
    tia_gain=TIA_GAIN_14_KOHM,
    rload=RLOAD_10_OHM,
    ref_source=REF_EXTERNAL,
    internal_zero=INTERNAL_ZERO_20_PERCENT,
    bias_sign=BIAS_SIGN_NEGATIVE,
    bias=BIAS_0_PERCENT,
    fet_short=FET_SHORT_DISABLED,
    op_mode=OP_MODE_3LEAD_AMP_CELL,
)

# SGX-4NO2 — Nitrogen Dioxide
SENSOR_NO2 = SensorConfig(
    nano_amperes_per_ppm=-600.0,
    internal_zero_calibration=0,
    ads_gain=ADS_GAIN_2_048V,
    tia_gain=TIA_GAIN_35_KOHM,
    rload=RLOAD_10_OHM,
    ref_source=REF_EXTERNAL,
    internal_zero=INTERNAL_ZERO_67_PERCENT,
    bias_sign=BIAS_SIGN_NEGATIVE,
    bias=BIAS_0_PERCENT,
    fet_short=FET_SHORT_DISABLED,
    op_mode=OP_MODE_3LEAD_AMP_CELL,
)

# SGX-4SO2 — Sulphur Dioxide
SENSOR_SO2 = SensorConfig(
    nano_amperes_per_ppm=400.0,
    internal_zero_calibration=0,
    ads_gain=ADS_GAIN_4_096V,
    tia_gain=TIA_GAIN_120_KOHM,
    rload=RLOAD_10_OHM,
    ref_source=REF_EXTERNAL,
    internal_zero=INTERNAL_ZERO_20_PERCENT,
    bias_sign=BIAS_SIGN_POSITIVE,
    bias=BIAS_0_PERCENT,
    fet_short=FET_SHORT_DISABLED,
    op_mode=OP_MODE_3LEAD_AMP_CELL,
)

# SGX-403-20 — Ozone
SENSOR_O3 = SensorConfig(
    nano_amperes_per_ppm=-1000.0,
    internal_zero_calibration=-0.0012,
    ads_gain=ADS_GAIN_2_048V,
    tia_gain=TIA_GAIN_35_KOHM,
    rload=RLOAD_10_OHM,
    ref_source=REF_EXTERNAL,
    internal_zero=INTERNAL_ZERO_67_PERCENT,
    bias_sign=BIAS_SIGN_NEGATIVE,
    bias=BIAS_0_PERCENT,
    fet_short=FET_SHORT_DISABLED,
    op_mode=OP_MODE_3LEAD_AMP_CELL,
)

# SGX-4NO-250 — Nitric Oxide
SENSOR_NO = SensorConfig(
    nano_amperes_per_ppm=400.0,
    internal_zero_calibration=0,
    ads_gain=ADS_GAIN_4_096V,
    tia_gain=TIA_GAIN_120_KOHM,
    rload=RLOAD_10_OHM,
    ref_source=REF_EXTERNAL,
    internal_zero=INTERNAL_ZERO_20_PERCENT,
    bias_sign=BIAS_SIGN_POSITIVE,
    bias=BIAS_12_PERCENT,
    fet_short=FET_SHORT_DISABLED,
    op_mode=OP_MODE_3LEAD_AMP_CELL,
)

# SGX-4H2S-100 — Hydrogen Sulphide
SENSOR_H2S = SensorConfig(
    nano_amperes_per_ppm=1200.0,
    internal_zero_calibration=0,
    ads_gain=ADS_GAIN_4_096V,
    tia_gain=TIA_GAIN_7_KOHM,
    rload=RLOAD_10_OHM,
    ref_source=REF_EXTERNAL,
    internal_zero=INTERNAL_ZERO_20_PERCENT,
    bias_sign=BIAS_SIGN_POSITIVE,
    bias=BIAS_0_PERCENT,
    fet_short=FET_SHORT_DISABLED,
    op_mode=OP_MODE_3LEAD_AMP_CELL,
)

# SGX-4NH3-300 — Ammonia
SENSOR_NH3 = SensorConfig(
    nano_amperes_per_ppm=40.0,
    internal_zero_calibration=0,
    ads_gain=ADS_GAIN_4_096V,
    tia_gain=TIA_GAIN_35_KOHM,
    rload=RLOAD_10_OHM,
    ref_source=REF_EXTERNAL,
    internal_zero=INTERNAL_ZERO_20_PERCENT,
    bias_sign=BIAS_SIGN_POSITIVE,
    bias=BIAS_0_PERCENT,
    fet_short=FET_SHORT_DISABLED,
    op_mode=OP_MODE_3LEAD_AMP_CELL,
)

# SGX-4CL2 — Chlorine
SENSOR_CL2 = SensorConfig(
    nano_amperes_per_ppm=600.0,
    internal_zero_calibration=0,
    ads_gain=ADS_GAIN_4_096V,
    tia_gain=TIA_GAIN_120_KOHM,
    rload=RLOAD_33_OHM,
    ref_source=REF_EXTERNAL,
    internal_zero=INTERNAL_ZERO_20_PERCENT,
    bias_sign=BIAS_SIGN_POSITIVE,
    bias=BIAS_0_PERCENT,
    fet_short=FET_SHORT_DISABLED,
    op_mode=OP_MODE_3LEAD_AMP_CELL,
)


# ===========================================================================
# ElectrochemicalGasSensor
# ===========================================================================
class ElectrochemicalGasSensor:
    """
    MicroPython class for the Soldered Electrochemical Gas Sensor breakout.
    Combines ADS1115 (ADC) and LMP91000 (analog frontend) over I2C.
    Supports CO, NO2, SO2, O3, NO, H2S, NH3, CL2 sensor types.
    """

    def __init__(self, sensor_type, i2c=None, adc_addr=_DEFAULT_ADC_ADDR, config_pin=None):
        """
        Initialize the sensor.

        :param sensor_type: SensorConfig instance (SENSOR_CO, SENSOR_NO2, etc.)
        :param i2c: Initialized I2C object (optional, auto-detected on known boards)
        :param adc_addr: Legacy board: the ADS1115's own I2C address (0x48-0x4B).
                          ATtiny bridge board: the bridge's easyC address (0x30-0x37).
                          begin() picks the transport based on which range this falls in.
        :param config_pin: GPIO pin number for LMP91000 MENB (None if wired to GND).
                            Unused when running against a bridge board - LMPEN is
                            hardwired to GND on that board revision.
        """
        self._type = sensor_type
        self._adcAddr = adc_addr
        self._tiaGainInKOhms = 0.0
        self._internalZeroPercent = 0.0

        if i2c is not None:
            self._i2c = i2c
        else:
            if uname().sysname in ("esp32", "Soldered Dasduino CONNECTPLUS"):
                self._i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            elif uname().sysname == "esp8266":
                self._i2c = I2C(scl=Pin(5), sda=Pin(4))
            else:
                raise Exception("Board not recognized, please pass an I2C object manually")

        # MENB: HIGH = LMP91000 I2C disabled (normal op), LOW = enabled (config mode)
        self._configPin = Pin(config_pin, Pin.OUT, value=1) if config_pin is not None else None

    def begin(self):
        """
        Initialize the sensor's transport and configure the analog frontend.
        Must be called before making any readings.

        Auto-detects legacy direct-wired boards vs. new ATtiny bridge boards
        from which address range adc_addr falls in (see __init__ docstring).

        :returns: True if successful, False if initialization failed
        """
        self._bridgeMode = _BRIDGE_ADDR_MIN <= self._adcAddr <= _BRIDGE_ADDR_MAX

        if not self._bridgeMode:
            self._lmp = LMP91000(self._i2c)
            self._ads = ADS1115(self._i2c, self._adcAddr)

            result = self._ads.begin()
            self._ads.setGain(self._type.adsGain)
            self._ads.setDataRate(0)  # slowest for best precision
        else:
            # ads is math-only here (toVoltage()/setGain() never touch i2c) - it
            # never issues any I2C traffic of its own in bridge mode.
            self._ads = ADS1115(self._i2c, self._adcAddr)
            self._ads.setGain(self._type.adsGain)
            self._ads.setDataRate(0)

            result = self._pingBridge()
            result = result and self._sendConfigureAdc(self._type.adsGain, 0)
            # config_pin is unused here - LMPEN is hardwired to GND on the bridge board.

        result = result and bool(self._configureLMP())
        return result

    def configureLMP(self):
        """Re-configure the LMP91000. Useful after power cycle."""
        return self._configureLMP()

    def _configureLMP(self):
        tiacn = (self._type.TIA_GAIN_IN_KOHMS << 2) | self._type.RLOAD
        refcn  = ((self._type.REF_SOURCE    << 7) |
                  (self._type.INTERNAL_ZERO << 5) |
                  (self._type.BIAS_SIGN     << 4) |
                   self._type.BIAS)
        modecn = (self._type.FET_SHORT << 7) | self._type.OP_MODE

        if self._bridgeMode:
            res = self._sendConfigureLmp(tiacn, refcn, modecn)
        else:
            if self._configPin is not None:
                self._configPin.value(0)  # MENB LOW — enable I2C config

            res = self._lmp.configure(tiacn, refcn, modecn)

            if self._configPin is not None:
                self._configPin.value(1)  # MENB HIGH — disable I2C config

        self._tiaGainInKOhms      = _TIA_GAIN_TABLE.get(self._type.TIA_GAIN_IN_KOHMS, -1)
        self._internalZeroPercent = _INTERNAL_ZERO_TABLE.get(self._type.INTERNAL_ZERO, -1)

        return res

    def getVoltage(self):
        """Read current voltage from the ADS1115 (channel 0). Returns float in volts."""
        raw = self._triggerAndReadAdc() if self._bridgeMode else self._ads.readADC(0)
        return self._ads.toVoltage(raw)

    def _bridge_transaction(self, cmd, payload=b""):
        """
        Send a command to the ATtiny bridge and poll the 3-byte response until
        OK/ERROR or timeout.

        :note: Blocking - protocol is synchronous, one command in flight at a time.
               Only used when self._bridgeMode is True. Unlike Arduino's Wire library
               (which just returns a nonzero status on a non-ACK), MicroPython's
               machine.I2C raises OSError - treated here the same as a BUSY/not-ready
               response and retried until the timeout, instead of crashing outright.
        :returns: (ok, resultHigh, resultLow) tuple
        """
        start = time.ticks_ms()
        sent = False
        while time.ticks_diff(time.ticks_ms(), start) < _BRIDGE_TIMEOUT_MS:
            try:
                if not sent:
                    self._i2c.writeto(self._adcAddr, bytes([cmd]) + payload)
                    sent = True
                status, hi, lo = self._i2c.readfrom(self._adcAddr, 3)
            except OSError:
                time.sleep_ms(5)
                continue

            if status == _BRIDGE_STATUS_OK:
                return True, hi, lo
            if status == _BRIDGE_STATUS_ERROR:
                return False, 0, 0

            time.sleep_ms(5)  # still BUSY or no command registered yet - retry

        return False, 0, 0  # timeout

    def _pingBridge(self):
        ok, _, _ = self._bridge_transaction(_CMD_PING)
        return ok

    def _sendConfigureAdc(self, gain, data_rate):
        ok, _, _ = self._bridge_transaction(_CMD_CONFIGURE_ADC, bytes([gain, data_rate]))
        return ok

    def _sendConfigureLmp(self, tiacn, refcn, modecn):
        ok, _, _ = self._bridge_transaction(_CMD_CONFIGURE_LMP, bytes([tiacn, refcn, modecn]))
        return ok

    def _triggerAndReadAdc(self):
        ok, hi, lo = self._bridge_transaction(_CMD_TRIGGER_ADC)
        raw = (hi << 8) | lo
        if raw & 0x8000:
            raw -= 0x10000
        return raw

    def getPPM(self):
        """Calculate and return gas concentration in PPM."""
        voltage = self.getVoltage()

        volts_no_ref = voltage - (_REF_VOLTAGE * (self._internalZeroPercent / 100.0))
        volts_no_ref += self._type.internalZeroCalibration

        current = volts_no_ref / self._tiaGainInKOhms
        ppm = current / (self._type.nanoAmperesPerPPM * 1e-9)

        if ppm < 0:
            ppm = 0.0
        return ppm

    def getPPB(self):
        """Calculate and return gas concentration in PPB."""
        return self.getPPM() * 1000.0

    def getAveragedPPM(self, num_measurements=5, seconds_delay=2):
        """
        Average multiple PPM readings. Blocking.

        :param num_measurements: Number of readings to average
        :param seconds_delay: Seconds to wait between each reading
        :returns: Averaged PPM value
        """
        total = 0.0
        for _ in range(num_measurements):
            total += self.getPPM()
            time.sleep(seconds_delay)
        return total / num_measurements

    def getAveragedPPB(self, num_measurements=5, seconds_delay=2):
        """
        Average multiple PPB readings. Blocking.

        :param num_measurements: Number of readings to average
        :param seconds_delay: Seconds to wait between each reading
        :returns: Averaged PPB value
        """
        return self.getAveragedPPM(num_measurements, seconds_delay) * 1000.0

    def setCustomTiaGain(self, tia_gain):
        """Set custom TIA gain in Ohms (for external resistor use)."""
        self._tiaGainInKOhms = tia_gain

    def setCustomZeroCalibration(self, calibration):
        """Set custom zero-point calibration voltage offset."""
        self._type.internalZeroCalibration = calibration
