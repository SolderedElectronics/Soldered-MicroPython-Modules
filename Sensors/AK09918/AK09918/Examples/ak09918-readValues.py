# FILE: ak09918-readValues.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read X, Y, Z magnetic field values from the AK09918 in continuous
#        measurement mode and print them to the console
# WORKS WITH: 3-Axis Digital Compass AK09918 breakout: www.solde.red/333392
# LAST UPDATED: 2026-04-23

from machine import Pin, I2C
from ak09918 import AK09918
from ak09918_constants import AK09918_CONT_MEASURE_MODE1, AK09918_ERR_OK

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# compass = AK09918(i2c, mode=AK09918_CONT_MEASURE_MODE1)

# Initialize sensor over Qwiic in 10 Hz continuous measurement mode
compass = AK09918(mode=AK09918_CONT_MEASURE_MODE1)

print("AK09918 ready - reading at 10 Hz")
print("X (uT*10)\tY (uT*10)\tZ (uT*10)")

# Infinite loop
while True:
    # Wait until a new measurement is available
    if compass.isDataReady() != AK09918_ERR_OK:
        continue

    err, x, y, z = compass.getData()
    if err != AK09918_ERR_OK:
        print("Read error: {}".format(compass.strError(err)))
        continue

    # Print the X, Y, Z values
    print("{}\t\t{}\t\t{}".format(x, y, z))
