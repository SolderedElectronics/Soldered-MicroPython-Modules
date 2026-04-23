# FILE: pcal6416a-driveStrength.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Cycle through all four drive-strength levels on pin A0 and set port B to
#        open-drain mode. Drive strength controls how many output transistor pairs
#        drive the pin — higher values allow more current to be sourced or sunk.
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

expander.pinMode(PCAL6416A_A0, OUTPUT)

# Set port B (port 1) to open-drain — pin floats HIGH, pulls LOW when driven low
expander.openDrainPort(1, True)

expander.digitalWrite(PCAL6416A_A0, 1)  # Hold A0 HIGH throughout

while True:
    for strength in range(4):
        # 0 = weakest (fewest transistor pairs), 3 = strongest (most current)
        expander.driveStrength(PCAL6416A_A0, strength)
        print("Drive strength set to {}".format(strength))
        time.sleep(1)
