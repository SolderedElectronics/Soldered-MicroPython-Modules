# FILE: ButtonLedBuzzerBoard-fullDemo.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Full demo for Soldered Button, LED & Buzzer Board.
#        Prints button states, cycles LED colors every 2s, short beep on each change.
# WORKS WITH: Button, LED & Buzzer Board: solde.red/333182
# LAST UPDATED: 2026-05-20

from machine import I2C, Pin
import time
from ButtonLedBuzzerBoard import *

# Initialize I2C and the board
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
board = ButtonLedBuzzerBoard(i2c)

COLORS = [
    (255,   0,   0),  # red
    (  0, 255,   0),  # green
    (  0,   0, 255),  # blue
    (255, 255,   0),  # yellow
    (  0, 255, 255),  # cyan
    (255,   0, 255),  # magenta
    (255, 255, 255),  # white
    (  0,   0,   0),  # off
]

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Button, LED & Buzzer Board - Full Demo")
print("-----------------------------------------------")

board.setAllLEDs(0, 0, 0)
time.sleep_ms(2000)

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
color_idx = 0
last_color_change = time.ticks_ms()

while True:
    btn1 = "ON " if board.isButton1Pressed() else "off"
    btn2 = "ON " if board.isButton2Pressed() else "off"
    btn3 = "ON " if board.isButton3Pressed() else "off"
    print("BTN1:{} BTN2:{} BTN3:{}".format(btn1, btn2, btn3))

    if time.ticks_diff(time.ticks_ms(), last_color_change) > 2000:
        r, g, b = COLORS[color_idx]
        board.setAllLEDs(r, g, b)

        board.setBuzzer(2000)
        time.sleep_ms(100)
        board.setBuzzer(0)

        color_idx = (color_idx + 1) % len(COLORS)
        last_color_change = time.ticks_ms()

    time.sleep_ms(100)
