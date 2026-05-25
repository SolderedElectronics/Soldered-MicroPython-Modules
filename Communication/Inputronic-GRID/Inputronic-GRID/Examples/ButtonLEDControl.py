# FILE: ButtonLEDControl.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Example showing button-driven LED toggle on the Inputronic GRID.
#        Each button toggles its corresponding LED on or off.
#        First press turns the LED on in a row-specific color;
#        second press turns it off.
#        Demonstrates reading individual pads by row/col coordinate
#        and reacting with per-LED color control using the same coordinates.
# WORKS WITH: Inputronic GRID: www.soldered.com
# LAST UPDATED: 2026-05-12

from machine import I2C, Pin
from InputronicGrid import InputronicGrid
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# grid = InputronicGrid(i2c=i2c)

grid = InputronicGrid()
grid.clearLEDs()
print("Press any button to toggle its LED.")

# Toggle state per button, indexed by [row][col]
ledOn = [[False] * 4 for _ in range(4)]

# Colors per row (R, G, B)
rowColor = [
    (255,   0,   0),  # row 0 — red
    (  0, 255,   0),  # row 1 — green
    (  0,   0, 255),  # row 2 — blue
    (255, 128,   0),  # row 3 — orange
]

# Previous pad state per [row][col] for edge detection
prevState = [[False] * 4 for _ in range(4)]

while True:
    for row in range(4):
        for col in range(4):
            pressed = grid.readPad(row, col)

            if pressed and not prevState[row][col]:
                ledOn[row][col] = not ledOn[row][col]

                if ledOn[row][col]:
                    r, g, b = rowColor[row]
                    grid.setLED(row, col, r, g, b, 255)
                else:
                    grid.setLED(row, col, 0, 0, 0, 255)

                print("Button (row {}, col {}) → LED {}".format(
                    row, col, "ON" if ledOn[row][col] else "OFF"))

            prevState[row][col] = pressed

    time.sleep_ms(20)
