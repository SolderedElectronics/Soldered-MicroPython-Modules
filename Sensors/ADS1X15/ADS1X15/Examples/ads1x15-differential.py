# FILE: ads1x15-differential.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Hardware differential reads on ADS1015/ADS1115.
#        AIN0(+) vs AIN1(-) is the most common differential pair.
# WORKS WITH: ADS1015 / ADS1115 ADC Breakout
# LAST UPDATED: 2026-05-22
#
# Wiring:
#   - Connect ADS1015/ADS1115 via Qwiic / I2C (default address 0x48)
#   - Connect signal+ to AIN0, signal- to AIN1

from machine import I2C, Pin
import time
from ads1x15 import *

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
adc = ADS1115(i2c)

print("ADS1X15 Differential Example")

while not adc.begin():
    print("ADS1X15 not found. Check wiring! Retrying...")
    time.sleep_ms(1000)

adc.setGain(2)  # ±2.048 V — good for most differential signals

print("ADS1X15 initialized")
print("Reading AIN0(+) vs AIN1(-)")

while True:
    raw = adc.readADC_Differential_0_1()
    v   = adc.toVoltage(raw)
    print("Diff 0-1: raw={:6d}  voltage={:.4f} V".format(raw, v))
    time.sleep_ms(500)
