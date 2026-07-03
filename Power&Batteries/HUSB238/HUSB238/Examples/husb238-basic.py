# FILE: husb238-basic.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Reads PD attach status, negotiated voltage and current from HUSB238.
# WORKS WITH: HUSB238 USB-PD Sink Breakout: solde.red/333374
# LAST UPDATED: 2026-07-03

from machine import I2C, Pin
import time
from husb238 import HUSB238

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
husb238 = HUSB238(i2c)

while True:
    if husb238.isAttached():
        print(
            "Attached, voltage: {} V, current: {} A".format(
                husb238.getPDSrcVoltage(), husb238.getPDSrcCurrent()
            )
        )
    else:
        print("Not attached")

    time.sleep(1)
