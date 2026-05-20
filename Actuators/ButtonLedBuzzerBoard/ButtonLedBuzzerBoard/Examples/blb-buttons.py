# FILE: blb-buttons.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Button test - prints press and release events to serial.
# WORKS WITH: Button, LED & Buzzer Board: solde.red/333182
# LAST UPDATED: 2026-05-20

from machine import I2C, Pin
import time
from button_led_buzzer_board import *

# Initialize I2C and the board
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
board = ButtonLedBuzzerBoard(i2c)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Button, LED & Buzzer Board - Button Test")
print("Press any button...")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
last_buttons = 0

while True:
    buttons = board.readButtons()

    if buttons != last_buttons:
        for i in range(3):
            mask = 1 << i
            if (buttons & mask) and not (last_buttons & mask):
                print("BTN{} pressed".format(i + 1))
            elif not (buttons & mask) and (last_buttons & mask):
                print("BTN{} released".format(i + 1))
        last_buttons = buttons

    time.sleep_ms(20)
