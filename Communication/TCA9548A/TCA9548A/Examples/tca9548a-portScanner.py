# FILE: tca9548a-portScanner.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Scans all 8 TCA9548A channels for connected I2C devices.
#        Opens each channel in turn, probes all 128 addresses, and prints any
#        devices found. Repeats the full scan every 5 seconds.
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

while True:
    for channel in range(8):
        mux.openChannel(channel)
        print(f"TCA Port #{channel}")

        for addr in range(128):
            # Don't report on the TCA9548A itself
            if addr == 0x70:
                continue

            try:
                mux.i2c.writeto(addr, b"")
                print(f"  Found I2C 0x{addr:02X}")
            except OSError:
                pass  # No device at this address

        mux.closeChannel(channel)
        time.sleep(1)

    print("\nScan completed.")
    time.sleep(5)
