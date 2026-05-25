# FILE: electrochemical-customConfig.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Custom LMP91000 configuration example for any electrochemical sensor.
# WORKS WITH: Electrochemical Gas Sensor Breakout: solde.red/333218
# LAST UPDATED: 2026-05-21

# Connecting diagram:
#
# Electrochemical Gas Sensor    Dasduino
# Qwiic------------------------>Qwiic
# LMPEN------------------------>GPIO pin (see config_pin parameter below)

from machine import I2C, Pin
import time
from ElectrochemicalGasSensor import (
    ElectrochemicalGasSensor, SensorConfig,
    TIA_GAIN_35_KOHM, RLOAD_10_OHM, REF_EXTERNAL,
    INTERNAL_ZERO_67_PERCENT, BIAS_SIGN_NEGATIVE, BIAS_0_PERCENT,
    FET_SHORT_DISABLED, OP_MODE_3LEAD_AMP_CELL,
)
from ads1115 import ADS_GAIN_2_048V

# Custom sensor configuration — edit these values to match your sensor's datasheet.
#
# nanoAmperesPerPPM:      Sensitivity from the sensor datasheet (nA/PPM)
# internalZeroCalibration: Voltage offset added to zero the reading in clean air
# adsGain:                ADS1115 full-scale range (ADS_GAIN_6_144V .. ADS_GAIN_0_256V)
# tia_gain:               TIA feedback resistor (TIA_GAIN_2_75_KOHM .. TIA_GAIN_350_KOHM)
# rload:                  Load resistor (RLOAD_10_OHM .. RLOAD_100_OHM)
# ref_source:             Reference voltage source (REF_INTERNAL / REF_EXTERNAL)
# internal_zero:          Internal zero percentage (INTERNAL_ZERO_20/50/67_PERCENT or _BYPASSED)
# bias_sign:              Bias polarity (BIAS_SIGN_NEGATIVE / BIAS_SIGN_POSITIVE)
# bias:                   Bias percentage of Vref (BIAS_0_PERCENT .. BIAS_24_PERCENT)
# fet_short:              FET short (FET_SHORT_DISABLED / FET_SHORT_ENABLED)
# op_mode:                Operating mode (OP_MODE_3LEAD_AMP_CELL for normal operation)
SENSOR_CUSTOM = SensorConfig(
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

# Initialize I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

sensor = ElectrochemicalGasSensor(SENSOR_CUSTOM, i2c)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Electrochemical Gas Sensor - Custom Config Example")

if not sensor.begin():
    print("ERROR: Can't init the sensor! Check connections!")
    while True:
        time.sleep_ms(100)

print("Sensor initialized successfully!")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    reading = sensor.getPPB()

    print("Sensor reading: {:.5f} PPB".format(reading))

    time.sleep_ms(2500)
