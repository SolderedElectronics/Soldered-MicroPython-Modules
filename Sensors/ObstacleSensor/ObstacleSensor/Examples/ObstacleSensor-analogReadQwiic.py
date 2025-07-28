# FILE: ObstacleSensor-analogReadQwiic.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to get the distance value for the Qwiic version of
#         the obstacle sensor breakout board
# WORKS WITH: Obstacle sensor with Qwiic: www.solde.red/333004
# LAST UPDATED: 2025-06-18

from ObstacleSensor import ObstacleSensor  # Import the obstacle sensor class
import time  # Module used to pause the board
from machine import I2C, Pin

# Create an instance of the obstacle sensor object
sensor = ObstacleSensor()

# You can also define a custom I2C communication and address if needed:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# sensor=ObstacleSensor(i2c, address=0x32)

# Infinite loop
while 1:
    # Print the analog voltage read from the sensor
    print(sensor.analogRead())
    # Pause for 100ms
    time.sleep(0.1)
