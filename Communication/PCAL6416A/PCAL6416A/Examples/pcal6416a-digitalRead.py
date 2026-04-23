# FILE: pcal6416a-digitalRead.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read the state of a pin with an internal pull-up using the PCAL6416A IO expander.
#        Connect a pushbutton between pin A0 and GND — pressing it pulls the pin LOW.
# WORKS WITH: PCAL6416A IO Expander breakout: www.solde.red/333351
# LAST UPDATED: 2026-04-23

import time
from machine import Pin, I2C
from pcal6416a import PCAL6416A, PCAL6416A_A0, INPUT_PULLUP

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# expander = PCAL6416A(i2c)

# Initialize expander over Qwiic
expander = PCAL6416A()

# Set pin A0 as input with internal pull-up (pin reads HIGH when button is open)
expander.pinMode(PCAL6416A_A0, INPUT_PULLUP)

while True:
    state = expander.digitalRead(PCAL6416A_A0)
    print("State of pin A0 is: {}".format("HIGH" if state else "LOW"))
    time.sleep(1)
