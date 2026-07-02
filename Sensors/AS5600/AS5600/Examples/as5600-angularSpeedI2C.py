# FILE: as5600-angularSpeedI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read the angular speed of the magnet measured by AS5600, via I2C
# WORKS WITH: Position sensor AS5600 breakout: solde.red/333183
# LAST UPDATED: 2026-07-02

from as5600 import AS5600
import time

sensor = AS5600()  # Raises Exception if the sensor isn't found

while not sensor.magnetDetected():
    print("Magnet not detected!")
    time.sleep(1)

while True:
    print("\tw = {:.2f} deg/s".format(sensor.getAngularSpeed()))

    time.sleep(1)  # Wait before the next measurement, so output isn't too fast
