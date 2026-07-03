# FILE: husb238-requestVoltage.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Requests the PD source to switch output voltage.
# WORKS WITH: HUSB238 USB-PD Sink Breakout: solde.red/333374
# LAST UPDATED: 2026-07-03

from machine import I2C, Pin
import time
from husb238 import *

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
husb238 = HUSB238(i2c)

# Voltage to request from the source, one of 5, 9, 12, 15, 18, 20
REQUEST_VOLTAGE = 15

print("Requesting {} V...".format(REQUEST_VOLTAGE))

result = husb238.requestPD(REQUEST_VOLTAGE)
requestOk = False

if result == HUSB238_REQUEST_OK:
    print("Source switched voltage successfully")
    requestOk = True
elif result == HUSB238_REQUEST_UNSUPPORTED_VOLTAGE:
    print("Invalid voltage value, use 5/9/12/15/18/20")
elif result == HUSB238_REQUEST_NOT_OFFERED:
    print("Charger does not support this voltage")
elif result == HUSB238_REQUEST_REJECTED:
    print("Charger rejected the request")

while requestOk:
    print("Voltage: {} V, current: {} A".format(
        husb238.getPDSrcVoltage(), husb238.getPDSrcCurrent()))
    time.sleep(1)
