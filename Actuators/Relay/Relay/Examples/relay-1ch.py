# FILE: Relay-1ch.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: 1-channel relay control example - toggles relay on and off.
# WORKS WITH: Relay board (1CH): solde.red/333025
# LAST UPDATED: 2026-05-21

# Connecting diagram:
#
# Relay board    Dasduino
# Qwiic--------->Qwiic

from machine import I2C, Pin
import time
from Relay import Relay, CHANNEL1

# Initialize I2C and relay board
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
relay = Relay(i2c)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Relay Board - 1 Channel Control")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    # Turn on relay 1
    relay.relayControl(CHANNEL1, 1)
    print("Channel 1 state: {}".format(relay.getChannelState(CHANNEL1)))
    time.sleep_ms(1500)

    # Turn off relay 1
    relay.relayControl(CHANNEL1, 0)
    print("Channel 1 state: {}".format(relay.getChannelState(CHANNEL1)))
    time.sleep_ms(1500)
