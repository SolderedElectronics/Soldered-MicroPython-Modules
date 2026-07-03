# FILE: SliderPotentiometer-readValueQwiic.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Reads the value of potentiometer.
# WORKS WITH: SliderPotentiometer with Qwiic : www.solde.red/333131
# LAST UPDATED: 2026-04-30

import time
from SliderPotentiometer import QwiicSliderPotentiometer

slider = QwiicSliderPotentiometer()

while True:
    print("Raw value of slider potentiometer:", slider.get_value())
    print("Minimum value of slider potentiometer:", slider.min_value())
    print("Maximum value of slider potentiometer:", slider.max_value())
    print("Percent value of slider potentiometer:", slider.get_percentage())
    print()
    time.sleep(1)
