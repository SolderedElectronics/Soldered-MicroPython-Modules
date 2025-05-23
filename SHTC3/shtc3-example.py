# FILE: shtc3-example.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example for using the SHTC3 to measure temperature and humidity
# LAST UPDATED: 2025-05-23

from machine import Pin, I2C
from shtc3 import SHTC3
import time

# Initialize I2C (example for ESP32/ESP8266)
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# Initialize sensor
shtc3 = SHTC3(i2c)

while 1:
    #The sensor must sample the values before we can read them
    shtc3.sample()

    # Read values
    temperature=shtc3.readTemperature()
    humidity=shtc3.readHumidity()
    print("Temperature: {:.2f} C".format(temperature))
    print("Humidity: {:.2f} %\n".format(humidity))
    time.sleep(5.0)


