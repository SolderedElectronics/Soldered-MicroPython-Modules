# FILE: mcp4018-getDigipotI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Example - set wiper and read back raw value via I2C
# LAST UPDATED: 2026-05-26

from mcp4018 import MCP4018
from time import sleep

digipot = MCP4018()

while True:
    for pct in [0, 25, 50, 75, 100]:
        digipot.setWiperPercent(pct)
        print("Set: {}% | Raw value: {}".format(pct, digipot.getWiperValue()))
        sleep(5)
