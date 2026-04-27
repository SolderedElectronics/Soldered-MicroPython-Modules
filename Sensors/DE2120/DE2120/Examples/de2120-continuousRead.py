# FILE: de2120-continuousRead.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Example for reading barcodes in continuous mode — the scanner reads
#        automatically without needing startScan() calls
# WORKS WITH: Barcode scanner DE2120 breakout: www.solde.red/333182
# LAST UPDATED: 2026-04-23

from machine import UART
from de2120 import DE2120
import time

# Adjust tx and rx to match the pins you have wired on your board.
scanner = DE2120(tx=5, rx=4)

if not scanner.begin():
    print("DE2120 not detected. Check wiring.")
    raise SystemExit

# Enable continuous read with a 0.5 s repeat interval for the same barcode
scanner.enableContinuousRead(repeat_interval=2)

print("DE2120 in continuous read mode. Point at a barcode.")

while True:
    barcode = scanner.readBarcode()
    if barcode:
        print("Scanned:", barcode)
    time.sleep_ms(50)
