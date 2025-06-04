# FILE:ws2812b-blink-example.py
# AUTHOR: Soldered
# BRIEF: A simple example of blinking WS2812b LED's
# LAST UPDATED: 2025-05-26

import machine
import neopixel
import time

# === Configuration ===
PIN = 33         # GPIO pin
NUM_PIXELS = 24   # Number of LEDs on-board (Change as needed)

# === Setup ===
np = neopixel.NeoPixel(machine.Pin(PIN), NUM_PIXELS)

# === Function to set color (R, G, B) ===
def set_color(r, g, b):
    for i in range(NUM_PIXELS):
        np[i] = (r, g, b)
        np.write()

# === Blink loop ===
while True:
    set_color(255,255, 255)  # White color
    time.sleep(0.5)
    set_color(0,0,0) #Turn off
    time.sleep(0.5)
    
