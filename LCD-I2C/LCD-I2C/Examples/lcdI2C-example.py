# FILE: lcdI2C-example.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example of using LCD to write text, draw
#        custom characters and autoscroll
# LAST UPDATED: 2025-05-23

from machine import I2C, Pin
import time
import lcdI2C

i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=100000)

lcd = LCD_I2C(i2c)


lcd.backlight()
lcd.begin()

# Hello world example

lcd.setcursorOn(0, 0)
lcd.print("Hello, World!")
lcd.setcursorOn(0, 1)
lcd.print("Made by Soldered!")

time.sleep(5.0)

# Custom character example
happy = [
    0b00000,
    0b10001,
    0b00000,
    0b00000,
    0b10001,
    0b01110,
    0b00000,
    0b00000,
]

wow = [
    0b00000,
    0b10001,
    0b00000,
    0b01110,
    0b10001,
    0b01110,
    0b00000,
    0b00000,
]

anchor = [0b01110, 0b01010, 0b01110, 0b00100, 0b10101, 0b10101, 0b01110, 0b00100]

snow = [0b01000, 0b11101, 0b01011, 0b00001, 0b00100, 0b01110, 0b00100, 0b10000]

lcd.createChar(0, happy)
lcd.createChar(1, wow)
lcd.createChar(2, anchor)
lcd.createChar(3, snow)

lcd.clear()

lcd.setcursorOn(0, 0)
lcd.write(0)
lcd.write(1)
lcd.write(2)
lcd.write(3)

time.sleep(5.0)

# Autoscroll example

lcd.clear()
lcd.autoscroll()
lcd.print("This is an autoscrolling example hihi")
lcd.scrollDisplayLeft()
