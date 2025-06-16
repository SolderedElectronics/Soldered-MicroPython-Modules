# FILE: RotaryEncoder-rotaryCounter.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing all of the basic functionalities of the Rotary Encoder board
# WORKS WITH: Rotary encoder board with Qwiic: www.solde.red/333188
# LAST UPDATED: 2025-06-16

# Import all constants and the RotaryEncoder class from the module
from RotaryEncoder import *

# Create an instance of the RotaryEncoder over Qwiic
rotary = RotaryEncoder()

# If needed, you can also initialize the encoder with a custom address:
# rotary = RotaryEncoder(address=0x32)

# Infinite loop to continuously read encoder state
while 1:
    # Fetch the current state of the rotary encoder or button
    state = rotary.getState()

    # Check if the state is not idle
    if state != ROTARY_IDLE:
        # If button was clicked
        if state == BTN_CLICK:
            print("Button clicked.")

        # If the encoder was double clicked
        elif state == BTN_DOUBLE_CLICK:
            print("Button double clicked.")

        # If the encoder was pressed for long
        elif state == BTN_LONG_PRESS:
            print("Long press.")

        # The encoder goes into this state after the long press was released
        elif state == BTN_LONG_RELEASE:
            print("Long release.")

        # If the encoder was rotated clockwise
        elif state == ROTARY_CCW:
            print("Rotated counter-clockwise.")

        # If the encoder was rotated counter - clockwise
        elif state == ROTARY_CW:
            print("Rotated clockwise.")
