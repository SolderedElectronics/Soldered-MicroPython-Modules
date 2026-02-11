# FILE: keyboard_poll.py
# BRIEF: Polling + debug example for Soldered Inputronic Keyboard (PRESS only)
# LAST UPDATED: 2026-02-11

import time
from machine import I2C, Pin
from os import uname

from inputronic_keyboard import InputronicKeyboard


def make_i2c():
    # Match the style from your BMP280 example: auto pins for known boards
    if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
        return I2C(0, scl=Pin(22), sda=Pin(21))
    raise Exception("Board not recognized; create I2C manually and pass it in.")


def main():
    print()
    print("Soldered Inputronic Keyboard - Polling (PRESS Only)")
    print("Press any key to see its position and resolved output.\n")

    # Initialize I2C + keyboard
    i2c = make_i2c()
    try:
        kbd = InputronicKeyboard(i2c=i2c)
    except Exception as e:
        print("Keyboard not found. Check Qwiic/easyC connection.")
        print("Error:", e)
        while True:
            time.sleep_ms(250)

    print("Keyboard ready.\n")

    while True:
        # Process all pending events
        while kbd.events_available() > 0:
            ev = kbd.read_mapped_event()
            if ev is None:
                break

            is_release, row, col, label = ev

            # Ignore release events
            if is_release or label is None:
                continue

            # Resolved printable character (SHIFT handled internally)
            ch = kbd.label_to_char(label, apply_shift=True)

            # Print press information (similar to Arduino sketch)
            # Format: PRESS    Row: x   Col: y   Label: ...   Char: 'c' or (n/a)
            if ch is not None:
                print(
                    "PRESS\tRow:", row,
                    "\tCol:", col,
                    "\tLabel:", label,
                    "\tChar: '{}'".format(ch)
                )
            else:
                print(
                    "PRESS\tRow:", row,
                    "\tCol:", col,
                    "\tLabel:", label,
                    "\tChar: (n/a)"
                )

        time.sleep_ms(1)


# Run
main()