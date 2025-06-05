# FILE: APDS9960-proximity.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example of measuring object proximity with the APDS9960 sensor
# WORKS WITH: Color and gesture sensor APDS-9960 breakout: www.solde.red/333002
# LAST UPDATED: 2025-06-05 

from time import sleep

from machine import Pin, I2C

from apds9960 import *

# If you aren't using the Qwiic connector, manually enter your I2C pins
#i2c = I2C(sda=Pin(21), scl=Pin(22))
#apds = APDS9960(i2c)

#Initialize sensor over Qwiic
apds = APDS9960()

#Sets the lower threshold for proximity detection used to determine a “gesture start", from 0 to 255
apds.setProximityIntLowThreshold(130)

print("Proximity Sensor Test")
print("=====================")

apds.enableProximitySensor()

#Variable that keeps track of the last proximity reading
oval = -1
while True:
    #Pause for 250ms
    sleep(0.25)
    #Read the proximity from sensor, value from 0 to 255
    val = apds.readProximity()
    #Check if read value is atleast higher or lower by 2 from previous value
    if val >= oval+2 or val <=oval-2:
        #Print out the proximity
        print("proximity={}".format(val))
        #Set previous value as current value
        oval = val