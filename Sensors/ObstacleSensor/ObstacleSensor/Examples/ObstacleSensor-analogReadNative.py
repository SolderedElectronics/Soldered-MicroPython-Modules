# FILE: ObstacleSensor-analogReadNative.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to get the distance value for the Native version of
#         the obstacle sensor breakout board
# WORKS WITH: Obstacle sensor TCRT5000 breakout: www.solde.red/333012
# LAST UPDATED: 2025-06-18

from ObstacleSensor import ObstacleSensor  # Import the obstacle sensor class
import time  # Module used to pause the board

# Create an instance of the obstacle sensor object
sensor = ObstacleSensor(analog_pin=27)

# Infinite loop
while 1:
    # Print the analog voltage read from the sensor
    print(sensor.analogRead())
    # Pause for 100ms
    time.sleep(0.1)
