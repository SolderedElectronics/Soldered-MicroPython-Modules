# FILE: hx711-calibrate.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Calibration example - zeroes the load cell and prints offset-corrected readings.
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
print("HX711 Load Cell - Calibration Example")

# While calibrating - don't put any load on the load cell!
# It has to measure the signal without any weight so we know where zero is.
# 15 measurements are averaged to reduce noise.
print("Calibrating zero - keep load cell unloaded...")
hx711.setZero()
print("Zero set! You can now place weight on the load cell.")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    # Read the calibrated (offset-corrected) value
    # You may also call getOffsettedReading(n) to average n readings
    reading = hx711.getOffsettedReading()

    # Print the reading
    print("HX711 Reading: {}".format(reading))

    time.sleep_ms(200)
