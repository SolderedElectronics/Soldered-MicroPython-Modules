from machine import Pin, I2C
from bme280 import BME280
import time

# Initialize I2C (example for ESP32/ESP8266)
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# Initialize sensor
bme280 = BME280(i2c)

# Read values
while 1:
    temp, pres, hum = bme280.read_all_values()
    altitude = bme280.calculate_altitude()

    print("Temperature: {:.2f} °C".format(temp))
    print("Pressure: {:.2f} hPa".format(pres))
    print("Humidity: {:.2f} %".format(hum))
    print("Altitude: {:.2f} m".format(altitude))
    time.sleep(5.0)


