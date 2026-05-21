# FILE: relay-4ch.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: 4-channel relay control example - toggles each relay on and off in sequence.
# WORKS WITH: Relay board (4CH): solde.red/333025
# LAST UPDATED: 2026-05-21

# Connecting diagram:
#
# Relay board    Dasduino
# Qwiic--------->Qwiic

from machine import I2C, Pin
import time
from relay import Relay, CHANNEL1, CHANNEL2, CHANNEL3, CHANNEL4

# Initialize I2C and relay board
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
relay = Relay(i2c)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Relay Board - 4 Channel Control")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
channels = [CHANNEL1, CHANNEL2, CHANNEL3, CHANNEL4]

while True:
    for ch_num, channel in enumerate(channels, start=1):
        # Turn on channel
        relay.relayControl(channel, 1)
        print("Channel {} state: {}".format(ch_num, relay.getChannelState(channel)))
        time.sleep_ms(1500)

        # Turn off channel
        relay.relayControl(channel, 0)
        print("Channel {} state: {}".format(ch_num, relay.getChannelState(channel)))
        time.sleep_ms(1500)
