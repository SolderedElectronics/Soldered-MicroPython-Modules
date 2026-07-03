# FILE: max7219-basic.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Demonstrates scrolling text, static text, and pixel drawing
#        on a MAX7219/MAX7221 LED matrix display.
# WORKS WITH: 8x8 LED matrix MAX7219: www.solde.red/333151
# LAST UPDATED: 2026-05-06

from machine import SPI, Pin
import time
from max7219 import (MAX7219, PAROLA_HW, GENERIC_HW,
                         INTENSITY, ON, OFF, TSL)

# -------------------------------------------------------------------------
# Configuration — adjust these for your hardware
# -------------------------------------------------------------------------
NUM_DEVICES = 3          # Number of 8x8 modules daisy-chained
CS_PIN      = 5          # Chip select GPIO pin  (LOAD)
MODULE_TYPE = PAROLA_HW  # Parola hardware modules
 
# -------------------------------------------------------------------------
# Initialize SPI and the display
# -------------------------------------------------------------------------
spi = SPI(1, baudrate=8_000_000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23))   # CLK_PIN=18 (SCK), DATA_PIN=23 (MOSI)
cs  = Pin(CS_PIN, Pin.OUT, value=1)

mx = MAX7219(MODULE_TYPE, spi, cs, NUM_DEVICES)

# -------------------------------------------------------------------------
# Helper: draw a simple 8-row tall smiley face on device 0
# -------------------------------------------------------------------------
SMILEY = [
    0b00111100,  # col 0
    0b01000010,  # col 1
    0b10100101,  # col 2
    0b10000001,  # col 3
    0b10100101,  # col 4
    0b10011001,  # col 5
    0b01000010,  # col 6
    0b00111100,  # col 7
]

def draw_smiley():
    mx.clear()
    for col, val in enumerate(SMILEY):
        mx.setColumn(0, col, val)   # device 0, columns 0-7

def draw_checkerboard():
    mx.clear()
    for dev in range(NUM_DEVICES):
        for r in range(8):
            # Alternating bits per row, inverted every row
            mx.setRow(dev, r, 0xAA if r % 2 == 0 else 0x55)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("MAX7219 MicroPython demo")
print("Devices: {}".format(NUM_DEVICES))
print("-----------------------------------------------")

# Set a comfortable brightness (0-15)
mx.control(INTENSITY, 4)

# -------------------------------------------------------------------------
# Demo 1: Static text
# -------------------------------------------------------------------------
print("Static text...")
mx.clear()
mx.printText("Hi!")
time.sleep(2)

# -------------------------------------------------------------------------
# Demo 2: Smiley face bitmap
# -------------------------------------------------------------------------
print("Smiley face...")
draw_smiley()
time.sleep(2)

# -------------------------------------------------------------------------
# Demo 3: Checkerboard pattern
# -------------------------------------------------------------------------
print("Checkerboard...")
draw_checkerboard()
time.sleep(2)

# -------------------------------------------------------------------------
# Demo 4: Pixel sweep — light up every pixel one at a time
# -------------------------------------------------------------------------
print("Pixel sweep...")
mx.clear()
col_count = mx.getColumnCount()
for r in range(8):
    for c in range(col_count):
        mx.setPoint(r, c, True)
        time.sleep_ms(10)
time.sleep(1)

# -------------------------------------------------------------------------
# Demo 5: Scrolling text — loops forever
# -------------------------------------------------------------------------
MESSAGE     = "Hello from MicroPython!"
SCROLL_DELAY = 40   # ms per column shift — lower = faster

print("Scrolling: '{}'".format(MESSAGE))
print("(loops forever — press Ctrl+C to stop)")

while True:
    mx.scrollText(MESSAGE, delay_ms=SCROLL_DELAY)