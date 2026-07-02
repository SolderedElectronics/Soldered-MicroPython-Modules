# FILE: as5600-statusI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Read the status registers of AS5600, via I2C
# WORKS WITH: Position sensor AS5600 breakout: solde.red/333183
# LAST UPDATED: 2026-07-02

from as5600 import AS5600
import time

sensor = AS5600()  # Raises Exception if the sensor isn't found

while not sensor.magnetDetected():
    print("Magnet not detected!")
    time.sleep(1)

while True:
    # The status registers can offer valuable insight into the sensor's current state

    # Raw read of the status register (see figure 21 of the AS5600 datasheet)
    print("Status register:\t{}".format(hex(sensor.readStatus())))
    time.sleep(1)

    # Raw read of the configuration register (see figure 22 of the AS5600 datasheet)
    print("Config register:\t{}".format(hex(sensor.getConfiguration())))
    time.sleep(1)

    # Currently set automatic gain, should be 0x80 with a well-placed magnet
    print("Gain:\t{}".format(hex(sensor.readAGC())))
    time.sleep(1)

    # Whether a magnet is currently detected
    print("Detect:\t{}".format(sensor.magnetDetected()))
    time.sleep(1)

    # Whether the magnet is too strong or too weak for good measurements
    print("Magnet high:\t{}".format(sensor.magnetTooStrong()))
    print("Magnet low:\t{}".format(sensor.magnetTooWeak()))
    print()

    time.sleep(2)  # Wait before the next print, so output isn't too fast
