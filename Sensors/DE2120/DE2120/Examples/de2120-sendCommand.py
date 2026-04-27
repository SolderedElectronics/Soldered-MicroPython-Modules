# FILE: de2120-sendCommand.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Toggle Code ID prefix transmission on the DE2120 scanner.
#        When enabled, the scanner prepends a symbology identifier to every
#        scan (e.g. 'A' for Code 128, 'Q' for QR Code).
#        Type 'y' or 'n' in the REPL to enable or disable it.
#        Barcodes scanned while waiting are also printed.
# WORKS WITH: Barcode scanner DE2120 breakout: www.solde.red/333182
# LAST UPDATED: 2026-04-23

import sys
import uselect
from de2120 import DE2120
import time

scanner = DE2120(tx=5, rx=4)

if not scanner.begin():
    print("Scanner did not respond. Check wiring. Did you scan the POR232 barcode?")
    raise SystemExit

print("Scanner online!")

# Set up non-blocking stdin so we can poll for barcodes while waiting for input
poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)


def stdin_available():
    return bool(poll.poll(0))


def flush_stdin():
    while stdin_available():
        sys.stdin.read(1)


while True:
    flush_stdin()

    print()
    print("Transmit Code ID with barcode? (y/n)")
    print("-------------------------------------")
    print("Type 'y' or 'n', or scan a barcode:")

    while not stdin_available():
        barcode = scanner.readBarcode()
        if barcode:
            print("...")
            print("Code found:", barcode)
        time.sleep_ms(200)

    cmd = sys.stdin.read(1)

    if cmd == "y":
        print("Code ID will be displayed on scan")
        scanner.sendCommand("CIDENA", "1")
    elif cmd == "n":
        print("Code ID will NOT be displayed on scan")
        scanner.sendCommand("CIDENA", "0")
    else:
        print("Command not recognized")
