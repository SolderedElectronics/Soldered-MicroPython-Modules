# FILE: blb-leds.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: LED test - cycles each LED through red/green/blue individually, then all together.
# WORKS WITH: Button, LED & Buzzer Board: solde.red/333182
# LAST UPDATED: 2026-05-20

from machine import I2C, Pin
import time
from button_led_buzzer_board import *

# Initialize I2C and the board
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
board = ButtonLedBuzzerBoard(i2c)

board.setAllLEDs(0, 0, 0)

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    # Test each LED individually
    for i in range(3):
        board.setAllLEDs(0, 0, 0)
        board.setLED(i, 255,   0,   0); time.sleep_ms(400)  # red
        board.setLED(i,   0, 255,   0); time.sleep_ms(400)  # green
        board.setLED(i,   0,   0, 255); time.sleep_ms(400)  # blue

    # All LEDs together
    board.setAllLEDs(255,   0,   0); time.sleep_ms(500)  # red
    board.setAllLEDs(  0, 255,   0); time.sleep_ms(500)  # green
    board.setAllLEDs(  0,   0, 255); time.sleep_ms(500)  # blue
    board.setAllLEDs(255, 255, 255); time.sleep_ms(500)  # white
    board.setAllLEDs(  0,   0,   0); time.sleep_ms(500)  # off
