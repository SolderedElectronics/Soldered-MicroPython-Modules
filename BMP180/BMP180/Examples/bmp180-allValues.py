# FILE: bmp180-allValues.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example for the BME280 sensor that reads temperature and pressure,
# WORKS WITH: Pressure & temperature sensor BMP180 breakout: www.solde.red/333060
# LAST UPDATED: 2025-06-04
from machine import I2C, Pin #Import for manual pin configuration
from bmp180 import BMP180 #Import the module
import time #Used for the sleep() function

#If you're not using the Qwiic connector, manually configure your I2C connection
#i2c = I2C(1, scl=Pin(22), sda=Pin(21))
#bmp180 = BMP180(i2c)

#Create an instance of the sensor object
bmp180 = BMP180()

#Infinite loop
while 1:
    #Get tempreature and pressure readings from sensor
    temperature = bmp180.read_temperature()
    pressure = bmp180.read_pressure()
    
    #Print the measured values to the second decimal point
    print("Temperature: {:.2f} C".format(temperature))
    print("Pressure: {} hPa\n".format(pressure))
    
    #Pause for 5 seconds
    time.sleep(5.0)
