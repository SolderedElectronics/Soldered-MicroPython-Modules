# FILE: oled_type.py
# BRIEF: Live typing example for Inputronic Keyboard + Soldered SSD1306 (MicroPython)
# LAST UPDATED: 2026-02-11

import time
from inputronic_keyboard import InputronicKeyboard
from ssd1306 import SSD1306

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64
CHAR_W = 8
CHAR_H = 8
COLS = SCREEN_WIDTH // CHAR_W   # 16
ROWS = SCREEN_HEIGHT // CHAR_H  # 8


def redraw_oled(display, text):
    """
    Redraw screen from text buffer with newline + wrap support.
    Keeps last ROWS lines visible (simple terminal viewport).
    """
    # Build lines with wrap
    lines = []
    cur = ""

    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue

        cur += ch
        if len(cur) >= COLS:
            lines.append(cur[:COLS])
            cur = cur[COLS:]

    lines.append(cur)

    # Keep only last visible lines
    lines = lines[-ROWS:]

    # Draw
    display.fill(0)
    y = 0
    for ln in lines:
        # framebuf.text doesn't clip nicely if longer, so clip to COLS
        display.text(ln[:COLS], 0, y, 1)
        y += CHAR_H
    display.show()


def main():
    print()
    print("Soldered Inputronic Keyboard - OledType Example (MicroPython)")
    print("SPACE=' ' | BACK=Backspace | ENTER=Newline | CAPS=Toggle Case | SHIFT=Modifier")
    print()

    # Init OLED (your driver auto-inits I2C if not given)
    try:
        display = SSD1306()
    except Exception as e:
        print("OLED not found. Check I2C wiring.")
        print("Error:", e)
        while True:
            time.sleep_ms(250)

    # Init keyboard (it can share same bus; also auto-inits if not given,
    # but better to share I2C explicitly in a combined project)
    try:
        kbd = InputronicKeyboard(i2c=display.i2c)
    except Exception as e:
        print("Keyboard not found. Check Qwiic/easyC connection.")
        print("Error:", e)
        while True:
            time.sleep_ms(250)

    print("Keyboard and OLED ready. Start typing!\n")

    typed = []

    redraw_oled(display, "")

    while True:
        changed = False

        while kbd.events_available() > 0:
            ev = kbd.read_mapped_event()
            if ev is None:
                break

            is_release, row, col, label = ev
            if is_release or label is None:
                continue

            # SPACE
            if label == "SPACE":
                typed.append(" ")
                changed = True
                continue

            # BACK
            if label == "BACK":
                if typed:
                    typed.pop()
                    changed = True
                continue

            # ENTER -> newline
            if label == "ENTER":
                typed.append("\n")
                changed = True
                continue

            # CAPS / SHIFT ignored (handled internally)
            if label == "CAPS" or label == "SHIFT":
                continue

            # Printable
            ch = kbd.label_to_char(label, apply_shift=True)
            if ch is not None:
                typed.append(ch)
                changed = True

        if changed:
            text = "".join(typed)
            redraw_oled(display, text)
            print("Typed:", text)

        time.sleep_ms(1)


main()