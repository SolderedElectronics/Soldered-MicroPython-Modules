# FILE: ReadButtons.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Example showing how to read all 16 buttons on the Inputronic GRID.
#        Reads all 16 button states every 50 ms and prints a 4x4 grid map.
#        Pressed buttons show 'X'; released buttons show '.'.
# WORKS WITH: Inputronic GRID: www.soldered.com
# LAST UPDATED: 2026-05-12

from machine import I2C, Pin
from InputronicGrid import InputronicGrid
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# grid = InputronicGrid(i2c=i2c)

grid = InputronicGrid()

print("Inputronic GRID ready.\n")
grid.clearLEDs()

while True:
    print("+---------+")
    for row in range(4):
        print("| ", end="")
        for col in range(4):
            print("X " if grid.readPad(row, col) else ". ", end="")
        print("|")
    print("+---------+\n")

    time.sleep_ms(50)
