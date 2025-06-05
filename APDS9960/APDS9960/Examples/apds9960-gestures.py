# FILE: APDS9960-gestures.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example of detecting gestures with the APDS9960 sensor
# WORKS WITH: Color and gesture sensor APDS-9960 breakout: www.solde.red/333002
# LAST UPDATED: 2025-06-05 

from time import sleep

from machine import Pin, I2C

from apds9960 import *

import apds9960

# If you aren't using the Qwiic connector, manually enter your I2C pins
#i2c = I2C(sda=Pin(21), scl=Pin(22))
#apds = APDS9960(i2c)

#Initialize sensor over Qwiic
apds = APDS9960()

#Sets the lower threshold for proximity detection used to determine a “gesture start", from 0 to 255
apds.setProximityIntLowThreshold(50)

#Gives a string representation of a given detected gesture
dirs = {
    APDS9960_DIR_NONE: "none",
    APDS9960_DIR_LEFT: "left",
    APDS9960_DIR_RIGHT: "right",
    APDS9960_DIR_UP: "up",
    APDS9960_DIR_DOWN: "down",
    APDS9960_DIR_NEAR: "near",
    APDS9960_DIR_FAR: "far",
}


print("Gesture Test")
print("============")
apds.enableGestureSensor()

#Infinite loop
while 1:
    #Delay for 500ms
    sleep(0.5)
    #See if a gesture has been detected
    if apds.isGestureAvailable():
        #Read the sensed motion
        motion = apds.readGesture()
        #Print out the gesture
        print("Gesture={}".format(dirs.get(motion, "unknown")))