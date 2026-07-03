# FILE: mcp4018-serialControlI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Example - control wiper via serial +/- commands
# LAST UPDATED: 2026-05-26

import sys
from mcp4018 import MCP4018


def printWiper(digipot):
    print("Wiper value: {}".format(digipot.getWiperValue()))


digipot = MCP4018()
print("Send '+' to increment, '-' to decrement.")
printWiper(digipot)

while True:
    ch = sys.stdin.read(1)
    if ch == "+":
        digipot.increment()
    elif ch == "-":
        digipot.decrement()
    printWiper(digipot)
