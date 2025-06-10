# FILE: HallEffect-digitalQwiic.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example of detecting a magnetic field with the Hall Effect sensor
# WORKS WITH: Hall effect sensor breakout with digital output & easyC: www.solde.red/333081
# LAST UPDATED: 2025-06-10 

from HallEffect import HallEffectDigital
from time import sleep
# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# sensor = HallEffectDigital(i2c)

#Initialize sensor over I2C
sensor=HallEffectDigital()

#You can also set a custom I2C address in the initialization:
#sensor=HallEffectDigital(address=0x31)

#Infinite loop
while 1:

    #Check if magnetic field is present
    reading=sensor.getReading()
    #If it is, print it out to inform the user
    if(reading):
        print("Magnet detected!")
    #Pause for 1 second
    sleep(1.0)