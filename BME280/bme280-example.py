# FILE: bme280.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example for the BME280 sensor that reads temperature, humidity,
#        pressure and calculates the altitude using the pressure measurement
# LAST UPDATED: 2025-05-23
from machine import Pin, I2C
from bme280 import BME280
import time

# Initialize I2C (example for ESP32/ESP8266)
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# Initialize sensor
bme280 = BME280(i2c)

# Read values
while 1:
    temp, pres, hum = bme280.readAllValues()
    altitude = bme280.calculateAltitude()

    print("Temperature: {:.2f} °C".format(temp))
    print("Pressure: {:.2f} hPa".format(pres))
    print("Humidity: {:.2f} %".format(hum))
    print("Altitude: {:.2f} m".format(altitude))
    time.sleep(5.0)
