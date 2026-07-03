# FILE: hx711-deepSleep.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Deep sleep example - wakes HX711, reads once, then sleeps for 15 seconds.
# WORKS WITH: HX711 Load Cell amplifier: solde.red/333005
# LAST UPDATED: 2026-05-21

# Connecting diagram:
#
# HX711 load-cell amplifier    Dasduino
# Qwiic----------------------->Qwiic
#
# HX711 load-cell amplifier    Load-cell
# (E+)------------------------>RED
# (E-)------------------------>BLACK
# (A-)------------------------>GREEN
# (A+)------------------------>WHITE

from machine import I2C, Pin
import time
from hx711 import HX711

# Initialize I2C and HX711
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
hx711 = HX711(i2c)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("HX711 Load Cell - Deep Sleep Example")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    # Wake up the HX711 from deep sleep
    hx711.setDeepSleep(False)

    # Wait until it initializes fully
    time.sleep_ms(200)

    # Make raw reading and store in variable
    reading = hx711.getRawReading()

    # Print the reading
    print("HX711 Reading: {}".format(reading))

    # Place the HX711 in deep sleep
    hx711.setDeepSleep(True)

    # Wait a long while until the next reading
    time.sleep_ms(15000)
