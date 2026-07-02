# FILE: as5600-directionI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Change the rotation direction of AS5600, via I2C
# WORKS WITH: Position sensor AS5600 breakout: solde.red/333183
# LAST UPDATED: 2026-07-02

from as5600 import AS5600, DIR_COUNTERCLOCKWISE, RAW_TO_DEGREES
import time

sensor = AS5600()  # Raises Exception if the sensor isn't found

while not sensor.magnetDetected():
    print("Magnet not detected!")
    time.sleep(1)

# Set direction of angle increment to counterclockwise, can be changed in the loop too
sensor.setDirection(DIR_COUNTERCLOCKWISE)

while True:
    # Angle increases with counterclockwise rotation, decreases with clockwise rotation
    print("{}\t{:.2f}".format(sensor.readAngle(), sensor.rawAngle() * RAW_TO_DEGREES))

    time.sleep(1)
