# FILE: as5600-outputModeAnalogI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Set AS5600 to output an analog signal on OUT, and measure it directly
# WORKS WITH: Position sensor AS5600 breakout: solde.red/333183
# LAST UPDATED: 2026-07-02

from as5600 import AS5600, OUTMODE_ANALOG_90
from machine import ADC, Pin
from os import uname
import time

# Connect AS5600 OUT pin to ANALOG_PIN
ANALOG_PIN = 34  # set to an ADC-capable GPIO on your board

sensor = AS5600()  # Raises Exception if the sensor isn't found

while not sensor.magnetDetected():
    print("Magnet not detected!")
    time.sleep(1)

# AS5600_OUTMODE_ANALOG_90 is a reduced output range (10% to 90%)
# AS5600_OUTMODE_ANALOG_100 (default) is the full output range
sensor.setOutputMode(OUTMODE_ANALOG_90)

analogPin = ADC(Pin(ANALOG_PIN))
if uname().sysname in ("esp32", "Soldered Dasduino CONNECTPLUS"):
    analogPin.atten(ADC.ATTN_11DB)

while True:
    print("Angle: {}".format(sensor.readAngle()))
    print("AnalogRead: {}".format(analogPin.read()))

    time.sleep(1)
