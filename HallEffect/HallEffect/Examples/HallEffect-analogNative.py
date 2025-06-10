# FILE: HallEffect-analogNative.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example of getting the magnetic field value from the Hall Effect sensor
# WORKS WITH: Hall effect sensor breakout with analog output: www.solde.red/333079
# LAST UPDATED: 2025-06-10 

from HallEffect import HallEffectAnalog
from time import sleep

#Initialize the sensor in native mode by giving it the board pin connected to OUT pin
sensor=HallEffectAnalog(pin=34)

#Infinite loop
while 1:
    #Get raw voltage value on OUT pin
    analog=sensor.getReading()

    #Get the raw voltage value converted into milli Teslas
    reading=sensor.getMilliTeslas()

    #Print out the readings
    print("ADC reading:",analog)
    print("Magnetic field= ",reading,"mT")
    #Empty row
    print()
    #Pause for 1 second
    sleep(1.0)