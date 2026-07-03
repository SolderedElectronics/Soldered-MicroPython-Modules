# FILE: SliderPotentiometer-readValue.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Reads the value of potentiometer.
# WORKS WITH: SliderPotentiometer : www.solde.red/333130
# LAST UPDATED: 2026-04-30

import time
from SliderPotentiometer import AnalogSliderPotentiometer

# Change to your wiring
slider = AnalogSliderPotentiometer(pin=34)

while True:
    print("Raw value of slider potentiometer:", slider.get_value())
    print("Minimum value of slider potentiometer:", slider.min_value())
    print("Maximum value of slider potentiometer:", slider.max_value())
    print("Percent value of slider potentiometer:", slider.get_percentage())
    print()
    time.sleep(1)