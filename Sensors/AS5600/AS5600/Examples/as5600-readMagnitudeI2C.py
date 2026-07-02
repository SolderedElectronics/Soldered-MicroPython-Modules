# FILE: as5600-readMagnitudeI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read the CORDIC magnitude of AS5600, via I2C
# WORKS WITH: Position sensor AS5600 breakout: solde.red/333183
# LAST UPDATED: 2026-07-02

from as5600 import AS5600
import time

sensor = AS5600()  # Raises Exception if the sensor isn't found

while not sensor.magnetDetected():
    print("Magnet not detected!")
    time.sleep(1)

while True:
    # Magnitude correlates with the strength of the magnet's field vector
    print("Magnitude: {:.3f} mT".format(sensor.readMagnitude() * 0.001))

    time.sleep(0.25)
