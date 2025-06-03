# FILE: PirSensor-Qwiic-example.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example showing how to detect movement
#        via the PIR sensor over the Qwiic connector
# LAST UPDATED: 2025-05-23
from PirSensor import PIRSensor
import time

# Initialize the sensor at a specific address
pir = PIRSensor(address=0x30)  # By default the address is 0x30
pir.begin()  # Initialize I2C communication with the PIR sensor

# Infinite loop
while 1:
    # Check if the pir sensor is responding via I2C
    if pir.available():
        # If movement is detected, inform user
        if pir.get_state():
            # Set how long the delay from the sensor will be before alerting of movement
            pir.set_delay(1)
            print("Motion detected!")
            # Pause for 1 second
            time.sleep(1)
