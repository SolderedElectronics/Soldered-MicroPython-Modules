# FILE: ads1219-interrupt.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: DRDY pin interrupt-driven reads example for the ADS1219.
#        Uses DRDY falling-edge interrupt instead of polling the status register.
#        More efficient at high sample rates (1000 SPS).
#        Open Serial Plotter to visualize readings.
# WORKS WITH: 24-Bit ADC ADS1219 Breakout: solde.red/333380
# LAST UPDATED: 2026-05-19
#
# Wiring:
#   - Connect ADS1219 via Qwiic / I2C (default address 0x40)
#   - Connect DRDY breakout pad to an interrupt-capable pin (default pin 4)
#   - Connect signal to AIN0, GND to board GND
#   - External reference voltage on REFP/REFN (3.3V assumed)

from machine import I2C, Pin
import time
from ads1219 import *

INTERRUPT_PIN = 4  # Change to match your wiring

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
adc = ADS1219(i2c)

interrupt_seen = False

def data_ready_isr(pin):
    global interrupt_seen
    interrupt_seen = True

while not adc.begin():
    print("ADS1219 not found. Check wiring! Retrying...")
    time.sleep_ms(1000)

adc.setVoltageReference(ADS1219_VREF_EXTERNAL)
adc.setMux(ADS1219_MUX_SINGLE_0)
adc.setGain(ADS1219_GAIN_1)
adc.setDataRate(ADS1219_DR_1000SPS)
adc.setConversionMode(ADS1219_MODE_CONTINUOUS)

drdy_pin = Pin(INTERRUPT_PIN, Pin.IN)
drdy_pin.irq(trigger=Pin.IRQ_FALLING, handler=data_ready_isr)

adc.startSync()

while True:
    if interrupt_seen:
        interrupt_seen = False
        adc.readConversion()
        mV = adc.getConversionMillivolts(3300.0)
        print("{:.3f}".format(mV))
