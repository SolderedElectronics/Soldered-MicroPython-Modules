# FILE: ws2812b-pulse.py
# AUTHOR: Soldered
# BRIEF: An example of changing the LED brightness to get a pulse effect
# LAST UPDATED: 2025-05-26

import machine  # Used for accessing hardware components like GPIO pins
import neopixel  # Library for controlling WS2812B (NeoPixel) LED strips
import time  # Provides delay and sleep functions

# === Configuration ===
PIN = 33  # GPIO pin number connected to the data line of the WS2812B LED strip
NUM_PIXELS = 10  # Total number of LEDs in the strip (you can change this to match your setup)

# === Setup ===
# Create a NeoPixel object to control the LED strip
# machine.Pin(PIN) initializes the GPIO pin
# NUM_PIXELS tells NeoPixel how many LEDs it needs to manage
np = neopixel.NeoPixel(machine.Pin(PIN), NUM_PIXELS)

# Set the initial brightness level (1.0 is full brightness, 0.0 is off)
brightness_level = 1.0

# === Main Loop ===
# This loop continuously fades the brightness of the LEDs down to a low value, 
# pauses, then fades it back up to full brightness, creating a "breathing" or pulse effect.
while True:
    # === Fade Out Loop ===
    # Gradually reduce brightness until it's close to 0.1
    while brightness_level > 0.1:
        # Set all LEDs to white color (RGB: 255, 255, 255)
        for i in range(NUM_PIXELS):
            np[i] = (255, 255, 255)
        
        # Apply the current brightness level
        np.brightness(brightness_level)

        # Write the updated color and brightness values to the LED strip
        np.write()

        # Decrease brightness slightly for the next iteration
        brightness_level -= 0.01

        # Delay to make the fade effect visible (adjust for speed)
        time.sleep(0.1)

    # Pause at the dimmest point for a moment
    time.sleep(1)

    # === Fade In Loop ===
    # Gradually increase brightness back up to 1.0
    while brightness_level < 1.0:
        # Set all LEDs to white again
        for i in range(NUM_PIXELS):
            np[i] = (255, 255, 255)

        # Apply the current brightness level
        np.brightness(brightness_level)

        # Write changes to the LEDs
        np.write()

        # Increase brightness slightly for the next iteration
        brightness_level += 0.01

        # Delay to make the fade effect visible
        time.sleep(0.1)

    # Pause at full brightness before starting the next fade-out
    time.sleep(1)