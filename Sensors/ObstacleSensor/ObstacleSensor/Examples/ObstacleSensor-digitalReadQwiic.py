# FILE: ObstacleSensor-digitalReadNative.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing us the digital read function of the module to
#         detect an obstacle
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

# Note: The digital pin will go to a HIGH state when the voltage it detects is below a certain treshold,
#      that treshold can be configured via the function below:

sensor.setTreshold(128)  # The value can be between 0 and 1023

# Infinite loop
while 1:
    # Check if the digital pin is set to HIGH, which means an obstacle is detected
    if sensor.digitalRead():
        print("Obstacle detected!")
    # Pause for 100ms
    time.sleep(0.1)
