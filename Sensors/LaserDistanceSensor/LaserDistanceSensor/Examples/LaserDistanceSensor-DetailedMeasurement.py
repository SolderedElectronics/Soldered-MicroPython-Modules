# FILE: LaserDistanceSensor-DetailedMeasurement.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to initialize and read the sensor.
#         It takes readings of: 
#               - the distance (In millimeters), 
#               - status of the sensor (A string representation showing if the measurement failed or not),
#               - the peak signal (In Mega counts per second)
#               - the ambient light (In Mega counts per second)
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

#Infinite loop
while True:
    # Recieve all the data in the form of a tuple and hand it out to local variables
    range_mm, status, peakSignal, ambient = sensor.readDetailed()
    # Print out the gathered data to the console
    print("range: ", range_mm, "mm", "\t status:", status, "\t peak signal:", peakSignal, "MCPS \t ambient: ", ambient,"MCPS")
    # Pause for 50 milliseconds
    time.sleep_ms(50)