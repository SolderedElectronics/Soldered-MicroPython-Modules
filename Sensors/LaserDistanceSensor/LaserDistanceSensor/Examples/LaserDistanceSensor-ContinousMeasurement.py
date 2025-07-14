# FILE: LaserDistanceSensor-ContinousMeasurement.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to initialize and read the sensor.
#         The readings are in milimeters and are taken every 50ms
# WORKS WITH: Laser distance sensor VL53L1X breakout: www.solde.red/333064
# LAST UPDATED: 2025-07-14 

from machine import I2C, Pin
from VL53L1X import VL53L1X
import time

# Initialize the sensor
sensor = VL53L1X()

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# sensor = VL53L1X(i2c)

# Infinite loop
while True:
    # Print out the distance measurement for the sensor in millimeters
    print("range: ", sensor.read(),"mm")
    # Pause for 50 milliseconds
    time.sleep_ms(50)
