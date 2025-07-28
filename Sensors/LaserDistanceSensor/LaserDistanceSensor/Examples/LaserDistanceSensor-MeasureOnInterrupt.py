# FILE: LaserDistanceSensor-MeasureOnInterrupt.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to configure the sensor to 
#         initiate an interrupt when the millimeter measurement is within,
#         outside, below or above a certain threshold
# WORKS WITH: Laser distance sensor VL53L1X breakout: www.solde.red/333064
# LAST UPDATED: 2025-07-14 

from machine import I2C, Pin
from VL53L1X import VL53L1X
import time

# Global variable that checks if an interrupt was detected
detected = 0

# Function that executes when an interrupt happens
def my_interrupt_handler(pin):
    global detected
    # Set the variable to 1 if an interrupt was triggered
    detected = 1

# Initialize the sensor and define the interrupt pin as well as the handler function
# that will be called. The pin defined must be connected to the GPIO1 pin on the breakout board!
sensor = VL53L1X(interruptPin=34, interruptCallback=my_interrupt_handler)

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# sensor = VL53L1X(i2c, interruptPin=34, interruptCallback=my_interrupt_handler)


# Set the threshold when the interrupt will be triggered in a range of millimeters
# The window value can be the following:
#                                       - in (will be triggered if the range is within the threshold specified)
#                                       - out (will be triggered if the range is outside the threshold specified)
#                                       - above (triggered if the measurement is above the upper defined threshold)
#                                       - below (triggered if the measurement is below the lower defined threshold)
sensor.set_distance_threshold_interrupt(100, 300, window='out')  # Trigger when outside of 100–300mm

# Infinite loop
while True:
    # The sensor itself starts taking continous measurements, must be called when using interrupts
    sensor.start_ranging()
    # If the 'detected' variable was set to 1
    if detected:
        dist = sensor.read()  # Save the sensor measurement into a variable
        print("Object outside of range window!")
        print("Distance:", dist, "mm") # Print out the distance to the console

        detected = 0 # reset the detection variable