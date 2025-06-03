# FILE: bme280.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example for the BME280 sensor that reads temperature, humidity,
#        pressure and calculates the altitude using the pressure measurement
# LAST UPDATED: 2025-05-23
from machine import Pin, I2C
from bme280 import BME280
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
#i2c = I2C(0, scl=Pin(22), sda=Pin(21))
#bme280 = BME280(i2c)

# Initialize sensor over Qwiic
bme280 = BME280()

# Infinite loop
while 1:
    #Get the reading for the temperature, pressure and humidity from the sensor
    temp, pres, hum = bme280.readAllValues()

    #Calculate the altitude using the measured pressure
    altitude = bme280.calculateAltitude()

    #Print the values that were read with two decimal points
    print("Temperature: {:.2f} °C".format(temp))
    print("Pressure: {:.2f} hPa".format(pres))
    print("Humidity: {:.2f} %".format(hum))
    print("Altitude: {:.2f} m \n".format(altitude))
    time.sleep(5.0)
