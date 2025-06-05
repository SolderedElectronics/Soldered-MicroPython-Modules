# FILE: BME680-allValues.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to measure temperature, humidity, pressure,
#         gas resistance and calculate altitude using the BME680 breakout board
# WORKS WITH: Enviromental & air quality sensor BME680 breakout: www.solde.red/333035
# LAST UPDATED: 2025-06-05 

from bme680 import BME680
from machine import I2C, Pin
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# bme680 = BME680(i2c)

# Initialize sensor over Qwiic
bme680 = BME680()

# Infinite loop
while 1:
    # Read the temperature, humidity, pressure and gas values and store them in their respective variables
    temp, pres, hum, gas = bme680.readAllValues()
    
    # Values can also be read one by one:
    
    #temp=bme680.readTemperature()
    #hum=bme680.readHumidity()
    #pres=bme680.readPressure()
    #gas=bme680.readGas()
    
    # Calculate the altitude using the pressure read by the sensor
    altitude = bme680.calculateAltitude()

    # Print the measured values, each in their own line
    print("Temperature: {:.2f} °C".format(temp))
    print("Pressure: {:.2f} hPa".format(pres))
    print("Humidity: {:.2f} %".format(hum))
    print("Gas resistance: {:.2f} mohm".format(gas))
    print("Altitude: {:.2f} m \n".format(altitude))

    # Pause for 5 seconds
    time.sleep(5.0)