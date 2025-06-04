# FILE: ws2812b-simple-fade-example.py
# AUTHOR: Soldered
# BRIEF: A simple fade animation on WS2812b LED's
# LAST UPDATED: 2025-05-26

import machine         # For accessing hardware like GPIO
import neopixel        # NeoPixel/WS2812B control module
import time            # For delays

# === Configuration ===
PIN = 33               # GPIO pin connected to the data line of the WS2812B strip
NUM_PIXELS = 24        # Number of LEDs in the strip (adjust to your setup)

# === Setup ===
# Initialize NeoPixel object on the specified pin with the given number of LEDs
np = neopixel.NeoPixel(machine.Pin(PIN), NUM_PIXELS)

# === Fade Loop ===
# This loop creates a moving red gradient (fading tail) along the LED strip
while True:
    for j in range(NUM_PIXELS):           # Outer loop: shift the animation forward one LED at a time
        time.sleep(0.01)                  # Short delay to control overall speed
        for i in range(NUM_PIXELS):       # Inner loop: calculate and set brightness for each LED
            time.sleep(0.01)              # Additional delay for smoother visual effect

            # Calculate LED index based on current position (j) and brightness position (i)
            if j + i < NUM_PIXELS:
                np[i + j] = (i * 8, 0, 0)  # Set red intensity based on position (i), green and blue = 0
            else:
                np[(i + j) - NUM_PIXELS] = (i * 8, 0, 0)  # Wrap around when index exceeds strip length

        np.write()  # Update the LED strip with new values
