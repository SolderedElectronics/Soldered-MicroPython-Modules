# FILE: serial_type.py
# BRIEF: Live typing example for Soldered Inputronic Keyboard (MicroPython)
# LAST UPDATED: 2026-02-11

import time
from machine import I2C, Pin
from os import uname

from inputronic_keyboard import InputronicKeyboard


def make_i2c():
    # Auto I2C pins for known boards (same style as other examples)
    if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
        return I2C(0, scl=Pin(22), sda=Pin(21))
    raise Exception("Board not recognized; create I2C manually.")


def main():

    print()
    print("Soldered Inputronic Keyboard - SerialType (Polling)")
    print(
        "SPACE=' ' | BACK=Backspace | ENTER=Newline | CAPS=Toggle Case | SHIFT=Modifier"
    )
    print()

    # Init keyboard
    i2c = make_i2c()

    try:
        kbd = InputronicKeyboard(i2c=i2c)
    except Exception as e:
        print("Keyboard not found. Check Qwiic/easyC connection.")
        print("Error:", e)

        while True:
            time.sleep_ms(250)

    print("Keyboard initialized successfully!")
    print("Start typing below:\n")

    # Main loop
    while True:
        # Process all pending keyboard events
        while kbd.events_available() > 0:
            ev = kbd.read_mapped_event()
            if ev is None:
                break

            is_release, row, col, label = ev

            # Only key press
            if is_release or label is None:
                continue

            # -----------------------------
            # Special keys
            # -----------------------------

            # Space
            if label == "SPACE":
                print(" ", end="")
                continue

            # Backspace (terminal style)
            if label == "BACK":
                print("\b \b", end="")
                continue

            # New line
            if label == "ENTER":
                print()
                continue

            # CAPS + SHIFT (handled internally)
            if label == "CAPS" or label == "SHIFT":
                continue

            # -----------------------------
            # Printable characters
            # -----------------------------

            ch = kbd.label_to_char(label, apply_shift=True)
            if ch is not None:
                print(ch, end="")

        # Cooperative delay
        time.sleep_ms(1)


# Run
main()
