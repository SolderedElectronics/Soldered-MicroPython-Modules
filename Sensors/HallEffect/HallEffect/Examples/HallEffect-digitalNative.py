# FILE: HallEffect-digitalNative.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example of detecting a magnetic field with the Hall Effect sensor
# WORKS WITH: Hall effect sensor breakout with digital output: www.solde.red/333080
# LAST UPDATED: 2025-06-10

from HallEffect import HallEffectDigital
from time import sleep

# Initialize the sensor in native mode by giving it the board pin connected to OUT pin
sensor = HallEffectDigital(pin=34)

# Infinite loop
while 1:
    # Check if magnetic field is present
    reading = sensor.getReading()
    # If it is, print it out to inform the user
    if reading:
        print("Magnet detected!")
    # Pause for 1 second
    sleep(1.0)
