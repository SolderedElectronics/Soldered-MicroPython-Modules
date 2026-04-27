# FILE: pcal6416a-digitalWrite.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Blink an output pin on the PCAL6416A IO expander.
#        Connect an LED (with series resistor) between pin A0 and GND.
# WORKS WITH: PCAL6416A IO Expander breakout: www.solde.red/333351
# LAST UPDATED: 2026-04-23

import time
from machine import Pin, I2C
from pcal6416a import PCAL6416A, PCAL6416A_A0, OUTPUT

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# expander = PCAL6416A(i2c)

# Initialize expander over Qwiic
expander = PCAL6416A()

# Set pin A0 as output
expander.pinMode(PCAL6416A_A0, OUTPUT)

while True:
    expander.digitalWrite(PCAL6416A_A0, 1)  # Set HIGH
    time.sleep(1)
    expander.digitalWrite(PCAL6416A_A0, 0)  # Set LOW
    time.sleep(1)
