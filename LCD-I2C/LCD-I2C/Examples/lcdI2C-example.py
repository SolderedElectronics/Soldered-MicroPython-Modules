# FILE: lcdI2C-example.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example of using LCD to write text, draw
#        custom characters and autoscroll
# LAST UPDATED: 2025-05-23

from machine import I2C, Pin
import time
from lcdI2C import LCD_I2C

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# lcd = LCD_I2C(i2c)

# Initialize sensor over Qwiic
lcd = LCD_I2C()

# Turn on the backlight of the LCD
lcd.backlight()

# Start communication with the LCD over I2C
lcd.begin()

# Hello world example
# Sets the cursor to the first character place in the first row
lcd.setCursor(0, 0)
lcd.print("Hello, World!")
# Sets the cursor to the first character place in the second row
lcd.setCursor(0, 1)
lcd.print("Made by Soldered!")

time.sleep(5.0)

# Custom character example, Characters are in binary form, each row represents a row of pixels and a 1 represents that a pixel is turned on
# A smiley face :)
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

# A shocked face :o
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

# An anchor
anchor = [0b01110, 0b01010, 0b01110, 0b00100, 0b10101, 0b10101, 0b01110, 0b00100]

# A snowflake
snow = [0b01000, 0b11101, 0b01011, 0b00001, 0b00100, 0b01110, 0b00100, 0b10000]

# Write the defined c haracters into memory
lcd.createChar(0, happy)
lcd.createChar(1, wow)
lcd.createChar(2, anchor)
lcd.createChar(3, snow)

# Clear the screen
lcd.clear()

lcd.setCursor(0, 0)
lcd.write(0)
lcd.write(1)
lcd.write(2)
lcd.write(3)

time.sleep(5.0)

# Autoscroll example

lcd.clear()
sentence = "Autoscroll example"
# When autoscroll is enabled, the characters will scroll to the left to make room for oncoming characters
lcd.autoscroll()
# Set cursor to the last place in row
lcd.setCursor(16, 0)
# Go through each character in sentence and print one every second
for i in range(len(sentence)):
    # Display the character onto the screen
    lcd.print(sentence[i])
    time.sleep(1.0)
