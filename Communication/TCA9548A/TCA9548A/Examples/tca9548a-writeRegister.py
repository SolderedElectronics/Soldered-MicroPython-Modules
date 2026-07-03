# FILE: tca9548a-writeRegister.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Advanced example of how to write to the TCA9548A channel register directly.
#        Opens channels 0, 3, 4 & 7 simultaneously using a single writeRegister() call,
#        reads back the register to verify, then closes all channels and halts.
# WORKS WITH: I2C Multiplexer TCA9548A Breakout: www.solde.red/333077
# LAST UPDATED: 2026-04-30

from machine import I2C, Pin
from tca9548a import (
    TCA9548A,
    TCA_CHANNEL_0,
    TCA_CHANNEL_3,
    TCA_CHANNEL_4,
    TCA_CHANNEL_7,
)
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# mux = TCA9548A(i2c)

# Initialize expander over Qwiic
mux = TCA9548A()


mux.closeAll()  # Set a known base state on startup

print("\n--- Calculate Channel Byte (153) ---")
time.sleep_ms(500)

print("Adding Channels 0, 3, 4 & 7")
buff = 0x00
buff |= TCA_CHANNEL_0
buff |= TCA_CHANNEL_3
buff |= TCA_CHANNEL_4
buff |= TCA_CHANNEL_7  # Enable channels in buff variable
time.sleep_ms(500)

print(f"Writing Register: {buff}")
mux.writeRegister(buff)  # Write buff variable to register
time.sleep_ms(500)

print(f"Reading Register: {mux.readRegister()}")  # Read data from register
time.sleep_ms(500)

print("Closing Channels")
mux.closeAll()

# Halt — equivalent to Arduino's while(1==1)
while True:
    pass
