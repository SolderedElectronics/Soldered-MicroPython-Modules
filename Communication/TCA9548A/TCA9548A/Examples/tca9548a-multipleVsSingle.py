# FILE: tca9548a-multipleVsSingle.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Demonstrates the difference between single and multiple channel operation.
#        First opens each channel individually (closing before the next), then opens
#        all channels one by one without closing, accumulating them. The register value
#        is printed after each step to show the bitmask building up.
# WORKS WITH: I2C Multiplexer TCA9548A Breakout: www.solde.red/333077
# LAST UPDATED: 2026-04-30

from machine import I2C, Pin
from tca9548a import TCA9548A
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# mux = TCA9548A(i2c)

# Initialize expander over Qwiic
mux = TCA9548A()


mux.closeAll()  # Set a known base state on startup

while True:
    print("--- Opening single channels ---")
    for channel in range(8):
        print(f"Opening << Channel: {channel}")
        mux.openChannel(channel)
        time.sleep_ms(500)

        print(f"Register = Value: {mux.readRegister()}")
        time.sleep_ms(500)

        print(f"Closing >> Channel: {channel}")
        mux.closeChannel(channel)
        time.sleep_ms(500)

    print("--- Opening multiple channels ---")
    for channel in range(8):
        print(f"Opening << Channel: {channel}")
        mux.openChannel(channel)
        time.sleep_ms(500)

        print(f"Register = Value: {mux.readRegister()}")
        time.sleep_ms(500)

    print("Closing >> channels")
    mux.closeAll()
    time.sleep_ms(500)
