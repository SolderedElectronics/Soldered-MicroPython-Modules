# FILE: ObstacleSensor-digitalReadNative.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing us the digital read function of the module to
#         detect an obstacle
# WORKS WITH: Obstacle sensor TCRT5000 breakout: www.solde.red/333012
# LAST UPDATED: 2025-06-18

from ObstacleSensor import ObstacleSensor  # Import the obstacle sensor class
import time  # Module used to pause the board

# Create an instance of the obstacle sensor object
sensor = ObstacleSensor(digital_pin=27)

# Note: The digital pin will go to a HIGH state when the voltage it detects is below a certain treshold,
#      that treshold can be configured via the onboard potentiometer

# Infinite loop
while 1:
    # Check if the digital pin is set to HIGH, which means an obstacle is detected
    if sensor.digitalRead():
        print("Obstacle detected!")
    # Pause for 100ms
    time.sleep(0.1)
