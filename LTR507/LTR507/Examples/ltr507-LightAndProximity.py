# FILE: LTR507-LightAndProximity.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to initialize the LTR-507 sensor and get light and proximity measurements
# WORKS WITH: Digital light & proximity sensor LTR-507 breakout: www.solde.red/333063
# LAST UPDATED: 2025-06-10 

from machine import I2C, Pin
import time
from ltr507 import LTR507

"""
Connecting diagram:

IMPORTANT: an IR LED must be connected when measuring proximity!
LTR-507                      IR LED
VLED------------------------>CATHODE (-)
VCC------------------------->ANODE (+)
"""

# If you aren't using the Qwiic connector, manually enter your I2C pins
#i2c = I2C(0, scl=Pin(22), sda=Pin(21))
#sensor = LTR507(i2c)

#Initialize I2C communication with the sensor over Qwiic
sensor = LTR507()

#Set up the sensor with its default values
sensor.begin()

#Infinite loop
while 1:
    #Measure the light intensity from the sensor in lux 
    lux = sensor.getLightIntensity()
    #Measure the proximity value of the sensor
    prox = sensor.getProximity()
    
    #Print the values over Serial communication
    print("Lux:", lux, "Proximity:", prox)
    #Pause for 1 second
    time.sleep(1)
