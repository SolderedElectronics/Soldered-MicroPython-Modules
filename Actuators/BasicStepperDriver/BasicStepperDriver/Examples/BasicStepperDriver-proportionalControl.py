# FILE: BasicStepperDriver-proportionalControl.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Potentiometer controls motor position — motor follows pot value
# WORKS WITH: Basic Stepper Driver: www.solde.red/333250
# LAST UPDATED: 2026-05-25

# Wiring: connect a 10k linear potentiometer between 3.3V and GND,
# wiper to GPIO34 (or any ADC-capable pin on ESP32)
# Note: ESP32 ADC returns 0-4095 (12-bit), unlike Arduino (0-1023)

from BasicStepperDriver import BasicStepper
from machine import ADC, Pin

ANALOG_IN = ADC(Pin(34))
ANALOG_IN.atten(ADC.ATTN_11DB)   # Full 0-3.3V range

stepper = BasicStepper(BasicStepper.FULL4WIRE, 12, 13, 14, 15)
stepper.setMaxSpeed(1000)

while True:
    analog_in = ANALOG_IN.read()   # 0-4095
    stepper.moveTo(analog_in)
    stepper.setSpeed(100)
    stepper.runSpeedToPosition()
