# FILE:ws2812b-simple-fade-example.py
# AUTHOR: Soldered
# BRIEF: A simple fade animation on WS2812b LED's
# LAST UPDATED: 2025-05-26

import machine
import neopixel
import time

# === Configuration ===
PIN = 33         # GPIO pin
NUM_PIXELS = 24   # Number of LEDs on-board (Change as needed)

# === Setup ===
np = neopixel.NeoPixel(machine.Pin(PIN), NUM_PIXELS)

# === Fade Loop ===
while True:
    for j in range (NUM_PIXELS):
        time.sleep(0.01)
        for i in range (NUM_PIXELS):
            time.sleep(0.01)
            if j+i<NUM_PIXELS:
                np[i+j]=(i*8,0,0)
            else:
                np[(i+j)-NUM_PIXELS]=(i*8,0,0)
        np.write()