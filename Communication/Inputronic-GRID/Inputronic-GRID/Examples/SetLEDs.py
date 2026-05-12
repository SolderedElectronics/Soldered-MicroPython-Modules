# FILE: SetLEDs.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Example showing LED control on the Inputronic GRID.
#        Demonstrates three LED control methods in sequence:
#          1. Sweep each LED individually through red, green, and blue.
#          2. Fill all 16 LEDs with a single color (solid fills).
#          3. Animate a color rotation across all 16 LEDs using a bitmask.
# WORKS WITH: Inputronic GRID: www.soldered.com
# LAST UPDATED: 2026-05-12

from machine import I2C, Pin
from inputronic_grid import InputronicGrid
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# grid = InputronicGrid(i2c=i2c)

grid = InputronicGrid()
grid.clearLEDs()

while True:
    # ── 1. Sweep individual LEDs ──────────────────────────────────────────
    for row in range(4):
        for col in range(4):
            grid.setLED(row, col, 255, 0, 0, 255)   # red
            time.sleep_ms(80)
            grid.setLED(row, col, 0, 255, 0, 255)   # green
            time.sleep_ms(80)
            grid.setLED(row, col, 0, 0, 255, 255)   # blue
            time.sleep_ms(80)
            grid.setLED(row, col, 0, 0, 0, 255)     # off

    # ── 2. Solid fills ────────────────────────────────────────────────────
    grid.setAllLEDs(255, 0,   0  ); time.sleep_ms(400)  # red
    grid.setAllLEDs(0,   255, 0  ); time.sleep_ms(400)  # green
    grid.setAllLEDs(0,   0,   255); time.sleep_ms(400)  # blue
    grid.setAllLEDs(255, 255, 255); time.sleep_ms(400)  # white
    grid.clearLEDs();               time.sleep_ms(300)
