# FILE: blb-buzzer.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Buzzer test - plays a sweep of frequencies.
# WORKS WITH: Button, LED & Buzzer Board: solde.red/333182
# LAST UPDATED: 2026-05-20

from machine import I2C, Pin
import time
from button_led_buzzer_board import *

# Initialize I2C and the board
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
board = ButtonLedBuzzerBoard(i2c)

FREQUENCIES = [500, 1000, 2000, 3000, 4000]

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    for freq in FREQUENCIES:
        board.setBuzzer(freq)
        time.sleep_ms(400)
        board.setBuzzer(0)
        time.sleep_ms(200)

    time.sleep_ms(1000)
