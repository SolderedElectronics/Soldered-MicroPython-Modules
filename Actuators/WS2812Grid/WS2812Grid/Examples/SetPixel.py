# FILE: SetPixel.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Basic usage: set individual pixels by (x, y) coordinates on the
#        Soldered 8x8 WS2812B LED grid.
#        Connect the grid data line to the pin defined below.
#        (0, 0) is top-left. X increases to the right, Y increases downward.
# WORKS WITH: Soldered WS2812B LED Grid: www.soldered.com
# LAST UPDATED: 2026-05-12

from machine import Pin
from ws2812_grid import WS2812Grid

PIN = Pin(6, Pin.OUT)

grid = WS2812Grid(PIN)
grid.begin()

# Set overall brightness (0 = off, 255 = full).
# Keep this low to avoid excessive current draw.
grid.setBrightness(40)

# Draw a red pixel at the top-left corner
grid.setPixel(0, 0, 255, 0, 0)

# Draw a green pixel at the top-right corner
grid.setPixel(7, 0, 0, 255, 0)

# Draw a blue pixel at the bottom-left corner
grid.setPixel(0, 7, 0, 0, 255)

# Draw a white pixel in the centre using a packed color
grid.setPixel(3, 3, WS2812Grid.Color(255, 255, 255))
grid.setPixel(4, 4, WS2812Grid.Color(255, 255, 255))

# Push all changes to the hardware
grid.show()

# Nothing to do — pixels stay lit
