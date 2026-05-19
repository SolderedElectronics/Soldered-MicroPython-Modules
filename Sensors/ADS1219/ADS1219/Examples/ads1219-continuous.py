# FILE: ads1219-continuous.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Continuous ADC conversion example for the ADS1219.
#        Puts the ADC into continuous mode — conversions run back-to-back
#        automatically. Polls the data-ready flag and prints the differential
#        voltage between AIN0(+) and AIN1(-) in millivolts.
# WORKS WITH: 24-Bit ADC ADS1219 Breakout: solde.red/333380
# LAST UPDATED: 2026-05-19
#
# Wiring:
#   - Connect ADS1219 via Qwiic / I2C (default address 0x40)
#   - Connect signal to AIN0 and AIN1 (or GND for AIN1)
#   - External reference voltage on REFP/REFN (3.3V assumed)

from machine import I2C, Pin
import time
from ads1219 import *

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
adc = ADS1219(i2c)

print("ADS1219 Continuous Example")

while not adc.begin():
    print("ADS1219 not found. Check wiring! Retrying...")
    time.sleep_ms(1000)

adc.setVoltageReference(ADS1219_VREF_EXTERNAL)
adc.setConversionMode(ADS1219_MODE_CONTINUOUS)
adc.startSync()

print("ADS1219 initialized")
print("Reading differential voltage AIN0(+) vs AIN1(-)")

while True:
    while not adc.dataReady():
        time.sleep_ms(10)

    adc.readConversion()
    mV = adc.getConversionMillivolts(3300.0)

    print("Voltage (mV): {:.3f}".format(mV))
