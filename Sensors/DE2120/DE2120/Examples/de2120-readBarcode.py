# FILE: de2120-readBarcode.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read barcodes with the DE2120 scanner in manual trigger mode.
#        Press the button on the scanner breakout to trigger a scan.
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

print("DE2120 ready. Press the button on the scanner to read a barcode.")

while True:
    # The scanner sends data when its physical button is pressed —
    # just poll readBarcode() and print whatever arrives.
    barcode = scanner.readBarcode()
    if barcode:
        print("Scanned:", barcode)
    time.sleep_ms(20)
