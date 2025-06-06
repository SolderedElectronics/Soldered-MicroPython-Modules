# FILE: bme280-allValues.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example for the BME280 sensor that reads temperature, humidity,
#        pressure and calculates the altitude using the pressure measurement
# WORKS WITH: Enviromental sensor BME280 breakout: www.solde.red/333036
# LAST UPDATED: 2025-05-23
from machine import Pin, I2C
from bme280 import BME280
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# bme280 = BME280(i2c)

# Initialize sensor over Qwiic
bme280 = BME280()

# Infinite loop
while 1:
    # Read the temperature, humidity and pressure values and store them in their respective variables
    temp, pres, hum = bme280.readAllValues()
    # Calculate the altitude using the pressure read by the sensor
    altitude = bme280.calculateAltitude()

    # Print the measured values, each in their own line
    print("Temperature: {:.2f} °C".format(temp))
    print("Pressure: {:.2f} hPa".format(pres))
    print("Humidity: {:.2f} %".format(hum))
    print("Altitude: {:.2f} m".format(altitude))

    # Pause for 5 seconds
    time.sleep(5.0)
