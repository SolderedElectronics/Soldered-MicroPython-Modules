# FILE: ads1x15-continuous.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Continuous conversion mode with the async interface.
#        Starts a conversion, polls isReady(), reads getValue() without blocking.
# WORKS WITH: ADS1015 / ADS1115 ADC Breakout
# LAST UPDATED: 2026-05-22
#
# Wiring:
#   - Connect ADS1015/ADS1115 via Qwiic / I2C (default address 0x48)

from machine import I2C, Pin
import time
from ads1x15 import *

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
adc = ADS1115(i2c)

print("ADS1X15 Continuous Mode Example")

while not adc.begin():
    print("ADS1X15 not found. Check wiring! Retrying...")
    time.sleep_ms(1000)

adc.setGain(0)
adc.setMode(0)      # continuous conversion
adc.requestADC(0)   # start first conversion on AIN0

print("ADS1X15 initialized, continuous mode")

while True:
    if adc.isReady():
        raw = adc.getValue()
        v   = adc.toVoltage(raw)
        print("AIN0: raw={:6d}  voltage={:.4f} V".format(raw, v))
        adc.requestADC(0)   # re-arm next conversion
    time.sleep_ms(10)
