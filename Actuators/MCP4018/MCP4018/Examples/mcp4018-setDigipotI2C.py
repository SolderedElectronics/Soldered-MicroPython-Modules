# FILE: mcp4018-setDigipotI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Example - set wiper percent via I2C
# LAST UPDATED: 2026-05-26

from mcp4018 import MCP4018
from time import sleep

digipot = MCP4018()

while True:
    for pct in [0, 25, 50, 75, 100]:
        digipot.setWiperPercent(pct)
        print("Wiper set to {}%".format(pct))
        sleep(5)
