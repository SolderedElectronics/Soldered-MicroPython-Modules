# FILE: Animations.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Demonstrates row sweep and colour-cycle animations on the
#        Soldered 8x8 WS2812B LED grid.
#        Connect the grid data line to the pin defined below.
# WORKS WITH: Soldered WS2812B LED Grid: www.soldered.com
# LAST UPDATED: 2026-05-12

from machine import Pin
from ws2812_grid import WS2812Grid
import time

PIN = Pin(6, Pin.OUT)

grid = WS2812Grid(PIN)
grid.begin()
grid.setBrightness(40)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def colorWheel(pos):
    """Simple HSV-to-RGB wheel: hue 0-255."""
    pos = 255 - pos
    if pos < 85:
        return WS2812Grid.Color(255 - pos * 3, 0, pos * 3)
    if pos < 170:
        pos -= 85
        return WS2812Grid.Color(0, pos * 3, 255 - pos * 3)
    pos -= 170
    return WS2812Grid.Color(pos * 3, 255 - pos * 3, 0)


# ---------------------------------------------------------------------------
# Animations
# ---------------------------------------------------------------------------

def rowSweep():
    for y in range(8):
        grid.clear()
        for x in range(8):
            grid.setPixel(x, y, 0, 180, 255)
        grid.show()
        time.sleep_ms(80)


def rainbowGrid(cycles):
    for _ in range(cycles):
        for hue in range(256):
            for y in range(8):
                for x in range(8):
                    offset = (x + y * 2) & 0xFF
                    grid.setPixel(x, y, colorWheel((hue + offset) & 0xFF))
            grid.show()
            time.sleep_ms(10)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

while True:
    rowSweep()
    time.sleep_ms(200)
    rainbowGrid(2)
    time.sleep_ms(200)
