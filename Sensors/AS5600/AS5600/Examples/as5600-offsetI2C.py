# FILE: as5600-offsetI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Demonstration of how to apply an offset to AS5600, via I2C
# WORKS WITH: Position sensor AS5600 breakout: solde.red/333183
# LAST UPDATED: 2026-07-02

from as5600 import AS5600, RAW_TO_DEGREES
import time

sensor = AS5600()  # Raises Exception if the sensor isn't found

while not sensor.magnetDetected():
    print("Magnet not detected!")
    time.sleep(1)

while True:
    sensor.setOffset(0)  # Reset the offset to 0
    print("Measurement without offset:\t{:.2f}".format(sensor.rawAngle() * RAW_TO_DEGREES))

    sensor.setOffset(45)  # Set offset to 45 degrees
    print("Measurement with offset:\t{:.2f}".format(sensor.rawAngle() * RAW_TO_DEGREES))

    print()

    time.sleep(1)
