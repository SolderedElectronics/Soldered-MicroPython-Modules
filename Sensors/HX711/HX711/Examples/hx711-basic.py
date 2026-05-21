# FILE: hx711-basic.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Basic HX711 raw reading example - prints raw ADC value to serial.
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
print("HX711 Load Cell - Basic Raw Reading")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    reading = hx711.getRawReading()
    print("HX711 Reading: {}".format(reading))
    time.sleep_ms(200)
