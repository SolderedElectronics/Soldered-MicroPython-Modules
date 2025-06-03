# FILE:   PirSensor-Native-example.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to detect movement
#         via the PIR sensor over the DOUT pin
# LAST UPDATED: 2025-05-23
from PirSensor import PIRSensor
from machine import Pin
import time

# Initialize the PIR sensor
pir = PIRSensor(pin=Pin(13))
pir.begin()

while 1:
    # If movement is detected, the SOUT or DOUT pin will go into a HIGH state
    if pir.get_state():
        # Inform the user that motion was detected
        print("Motion detected!")
        # Pause for 1 second
        time.sleep(1)
