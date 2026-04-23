# FILE: de2120-serialSettings.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Interactive configuration menu for the DE2120 scanner.
#        Control scanning, flashlight, reticle, reading area, reading mode,
#        and symbologies from the REPL. Barcodes scanned while the menu is
#        displayed are also printed.
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

poll = uselect.poll()
poll.register(sys.stdin, uselect.POLLIN)

def stdin_available():
    return bool(poll.poll(0))

def flush_stdin():
    while stdin_available():
        sys.stdin.read(1)

def wait_for_key():
    """Block until a key is typed, printing any scanned barcodes in the meantime."""
    while not stdin_available():
        barcode = scanner.readBarcode()
        if barcode:
            print("...")
            print("Code found:", barcode)
        time.sleep_ms(200)
    return sys.stdin.read(1)

def menu_flashlight():
    flush_stdin()
    print()
    print("-------------------------------------")
    print("1) Enable Flashlight")
    print("2) Disable Flashlight")
    print("-------------------------------------")
    print("Select an option number:")

    cmd = wait_for_key()
    if cmd == '1':
        print("White scan light on")
        scanner.lightOn()
    elif cmd == '2':
        print("White scan light off")
        scanner.lightOff()
    else:
        print("Command not recognized")

def menu_reticle():
    flush_stdin()
    print()
    print("-------------------------------------")
    print("1) Enable Reticle")
    print("2) Disable Reticle")
    print("-------------------------------------")
    print("Select an option number:")

    cmd = wait_for_key()
    if cmd == '1':
        print("Red scan reticle on")
        scanner.reticleOn()
    elif cmd == '2':
        print("Red scan reticle off")
        scanner.reticleOff()
    else:
        print("Command not recognized")

def menu_reading_area():
    flush_stdin()
    print()
    print("-------------------------------------")
    print("1) Full Width (Default)")
    print("2) Center 80%")
    print("3) Center 60%")
    print("4) Center 40%")
    print("5) Center 20%")
    print("-------------------------------------")
    print("Select an option number:")

    cmd = wait_for_key()
    areas = {'1': 100, '2': 80, '3': 60, '4': 40, '5': 20}
    if cmd in areas:
        pct = areas[cmd]
        print("Scanning {}% of frame".format(pct))
        scanner.changeReadingArea(pct)
    else:
        print("Command not recognized")

def menu_reading_mode():
    flush_stdin()
    print()
    print("-------------------------------------")
    print("1) Manual Read Mode (Default)")
    print("2) Continuous Read Mode")
    print("3) Motion Sensor Mode")
    print("-------------------------------------")
    print("Select an option number:")

    cmd = wait_for_key()
    if cmd == '1':
        print("Manual Trigger Mode enabled")
        scanner.disableMotionSense()
    elif cmd == '2':
        print("Continuous Read Mode enabled")
        scanner.enableContinuousRead()
    elif cmd == '3':
        print("Motion Trigger Mode enabled")
        scanner.enableMotionSense()
    else:
        print("Command not recognized")

def menu_symbologies():
    flush_stdin()
    print()
    print("-------------------------------------")
    print("1) Enable All 1D Symbologies")
    print("2) Disable All 1D Symbologies")
    print("3) Enable All 2D Symbologies")
    print("4) Disable All 2D Symbologies")
    print("-------------------------------------")
    print("Select an option number:")

    cmd = wait_for_key()
    if cmd == '1':
        print("1D Symbologies enabled")
        scanner.enableAll1D()
    elif cmd == '2':
        print("1D Symbologies disabled")
        scanner.disableAll1D()
    elif cmd == '3':
        print("2D Symbologies enabled")
        scanner.enableAll2D()
    elif cmd == '4':
        print("2D Symbologies disabled")
        scanner.disableAll2D()
    else:
        print("Command not recognized")

while True:
    flush_stdin()

    print()
    print("DE2120 Barcode Scanner")
    print("-------------------------------------")
    print("1) Start Scan")
    print("2) Stop Scan")
    print("3) Enable/Disable Flashlight")
    print("4) Enable/Disable Aiming Reticle")
    print("5) Set Reading Area")
    print("6) Set Reading Mode")
    print("7) Enable/Disable Symbologies")
    print("-------------------------------------")
    print("Select an option number:")

    cmd = wait_for_key()

    if cmd == '1':
        scanner.startScan()
    elif cmd == '2':
        scanner.stopScan()
    elif cmd == '3':
        menu_flashlight()
    elif cmd == '4':
        menu_reticle()
    elif cmd == '5':
        menu_reading_area()
    elif cmd == '6':
        menu_reading_mode()
    elif cmd == '7':
        menu_symbologies()
    else:
        print("Command not recognized")
