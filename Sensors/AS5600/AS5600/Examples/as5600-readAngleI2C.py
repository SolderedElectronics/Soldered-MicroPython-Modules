# FILE: as5600-readAngleI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read the rotation position of the magnet measured by AS5600, via I2C
# WORKS WITH: Position sensor AS5600 breakout: solde.red/333183
# LAST UPDATED: 2026-07-02

from as5600 import AS5600, RAW_TO_DEGREES, RAW_TO_RADIANS
import time

sensor = AS5600()  # Raises Exception if the sensor isn't found

while not sensor.magnetDetected():
    print("Magnet not detected!")
    time.sleep(1)

while True:
    print("Raw angle value: {}".format(sensor.readAngle()))  # 0 to 4095
    print("Angle in degrees: {:.2f}".format(sensor.rawAngle() * RAW_TO_DEGREES))
    print("Angle in radians: {:.4f}".format(sensor.rawAngle() * RAW_TO_RADIANS))
    print()

    time.sleep(1)
