# FILE: ads1219-multiplexer.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Input multiplexer configuration example for the ADS1219.
#        Demonstrates single-ended and differential channel selection.
#        This example reads AIN0 vs GND. Change setMux() to switch channels.
# WORKS WITH: 24-Bit ADC ADS1219 Breakout: solde.red/333380
# LAST UPDATED: 2026-05-19
#
# Available mux options:
#   ADS1219_MUX_DIFF_P0_N1  AIN0(+) vs AIN1(-) (default)
#   ADS1219_MUX_DIFF_P2_N3  AIN2(+) vs AIN3(-)
#   ADS1219_MUX_DIFF_P1_N2  AIN1(+) vs AIN2(-)
#   ADS1219_MUX_SINGLE_0    AIN0 vs GND
#   ADS1219_MUX_SINGLE_1    AIN1 vs GND
#   ADS1219_MUX_SINGLE_2    AIN2 vs GND
#   ADS1219_MUX_SINGLE_3    AIN3 vs GND
#   ADS1219_MUX_SHORTED     AVDD/2 vs AVDD/2 (offset measurement)
#
# Wiring:
#   - Connect ADS1219 via Qwiic / I2C (default address 0x40)
#   - Connect signal to AIN0, GND to board GND
#   - External reference voltage on REFP/REFN (3.3V assumed)

from machine import I2C, Pin
import time
from ads1219 import *

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
adc = ADS1219(i2c)

print("ADS1219 Multiplexer Example")

while not adc.begin():
    print("ADS1219 not found. Check wiring! Retrying...")
    time.sleep_ms(1000)

adc.setVoltageReference(ADS1219_VREF_EXTERNAL)
adc.setMux(ADS1219_MUX_SINGLE_0)  # AIN0 vs GND

print("ADS1219 initialized")
print("Reading AIN0 vs GND")

while True:
    adc.startSync()

    while not adc.dataReady():
        time.sleep_ms(10)

    adc.readConversion()
    mV = adc.getConversionMillivolts(3300.0)

    print("Voltage (mV): {:.3f}".format(mV))
