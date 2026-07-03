# FILE: ads1x15-simple.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Minimal test — reads all 4 single-ended channels and prints voltage.
# WORKS WITH: ADS1015 / ADS1115 ADC Breakout
# LAST UPDATED: 2026-05-22
#
# Wiring:
#   - Connect ADS1015/ADS1115 via Qwiic / I2C (default address 0x48)
#   - ADDR pin → GND for 0x48

from machine import I2C, Pin
import time
from ads1x15 import *

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
adc = ADS1115(i2c)  # swap for ADS1015 if using 12-bit variant

print("ADS1X15 Simple Example")

while not adc.begin():
    print("ADS1X15 not found. Check wiring! Retrying...")
    time.sleep_ms(1000)

adc.setGain(0)  # ±6.144 V full scale

print("ADS1X15 initialized")

while True:
    raw = adc.readADC(0)
    v = adc.toVoltage(raw)
    print("AIN0: raw={:6d}  voltage={:.4f} V".format(raw, v))
    time.sleep_ms(500)
