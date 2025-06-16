# FILE: RotaryEncoder-rotaryCounter.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to count the steps the rotary encoder makes
#         as well as how to reset the count if needed using the push button
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
        
        # If button was clicked, reset the encoder count
        if state == BTN_CLICK:
            rotary.resetCount()
            print("Button clicked, Encoder count reset.")

        # If the encoder was rotated clockwise
        elif state == ROTARY_CW:
            count = rotary.getCount()
            print(f"Clockwise: {count}")

        # If the encoder was rotated counter-clockwise
        elif state == ROTARY_CCW:
            count = rotary.getCount()
            print(f"Counter-Clockwise: {count}")

        
        
