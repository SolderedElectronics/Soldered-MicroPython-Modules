# FILE: blb-button-interaction.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Press a button to light its LED and sound the buzzer.
#        BTN1 -> LED1 red 1000Hz, BTN2 -> LED2 green 2000Hz, BTN3 -> LED3 blue 3000Hz.
#        Multiple buttons can be pressed simultaneously; buzzer plays highest button's tone.
# WORKS WITH: Button, LED & Buzzer Board: solde.red/333182
# LAST UPDATED: 2026-05-20

from machine import I2C, Pin
import time
from button_led_buzzer_board import *

# Initialize I2C and the board
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
board = ButtonLedBuzzerBoard(i2c)

board.setAllLEDs(0, 0, 0)
board.setBuzzer(0)

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    buttons = board.readButtons()

    btn1 = bool(buttons & 0x01)
    btn2 = bool(buttons & 0x02)
    btn3 = bool(buttons & 0x04)

    board.setLED(0, 255 if btn3 else 0, 0, 0)
    board.setLED(1, 0, 255 if btn2 else 0, 0)
    board.setLED(2, 0, 0, 255 if btn1 else 0)

    if btn3:       board.setBuzzer(3000)
    elif btn2:     board.setBuzzer(2000)
    elif btn1:     board.setBuzzer(1000)
    else:          board.setBuzzer(0)

    time.sleep_ms(20)
