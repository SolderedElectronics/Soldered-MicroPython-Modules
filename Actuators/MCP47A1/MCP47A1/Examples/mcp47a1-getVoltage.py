# FILE: mcp47a1-getVoltage.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: This example sets desired voltage on DACs output and then reads set voltage from DAC and prints it.
#        You can use a voltmeter to measure volttage on DACs output.
# WORKS WITH: DAC 6-Bit 1-Channel MCP47A1 Breakout: www.solde.red/333052
# LAST UPDATED: 2026-04-29

import time
from mcp47a1 import MCP47A1

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# mcp47a1 = MCP47A1(i2c)

# Initialize DAC over Qwiic
mcp47a1 = MCP47A1()


def printVoltage(v):
    print("DAC output: {:.2f} V".format(v))


while True:
    mcp47a1.setVoltage(0)
    printVoltage(mcp47a1.getVoltage())
    time.sleep(2)

    mcp47a1.setVoltage(1)
    printVoltage(mcp47a1.getVoltage())
    time.sleep(2)

    mcp47a1.setVoltage(2.5)
    printVoltage(mcp47a1.getVoltage())
    time.sleep(2)

    mcp47a1.setVoltage(3.3)
    printVoltage(mcp47a1.getVoltage())
    time.sleep(2)
