# FILE: ws2812b-blink-example.py
# AUTHOR: Soldered
# BRIEF: A simple example of blinking WS2812b LED's
# LAST UPDATED: 2025-05-26

import machine         # For accessing GPIO pins
import neopixel        # Library to control WS2812b (NeoPixel) LEDs
import time            # For delay/sleep functions

# === Configuration ===
PIN = 33               # GPIO pin connected to the data line of the WS2812B LED strip
NUM_PIXELS = 24        # Number of LEDs in the strip (adjust this to match your setup)

# === Setup ===
# Create a NeoPixel object on the specified GPIO pin with the specified number of LEDs
np = neopixel.NeoPixel(machine.Pin(PIN), NUM_PIXELS)

# === Function to set all LEDs to a specified color (R, G, B) ===
def set_color(r, g, b):
    for i in range(NUM_PIXELS):  # Iterate over each LED
        np[i] = (r, g, b)         # Set the color for the current LED
        np.write()               # Update the strip (could be moved outside loop for efficiency)

# === Blink loop ===
# Continuously blink all LEDs on and off
while True:
    set_color(255, 255, 255)     # Turn all LEDs on to full white
    time.sleep(0.5)              # Wait 0.5 seconds
    set_color(0, 0, 0)           # Turn all LEDs off (black)
    time.sleep(0.5)              # Wait 0.5 seconds

    
