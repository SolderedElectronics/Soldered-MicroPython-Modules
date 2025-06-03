# FILE: shtc3-example.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example for using the SHTC3 to measure temperature and humidity
# WORKS WITH: Temperature and humidity sensor SHTC3 breakout: www.solde.red/333032
# LAST UPDATED: 2025-05-23

from machine import Pin, I2C
from shtc3 import SHTC3
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# shtc3 = SHTC3(i2c)

# Initialize sensor over Qwiic
shtc3 = SHTC3()


# Infinite loop
while 1:
    # The sensor must sample the values before we can read them
    shtc3.sample()

    # Read the temperature and humidity values that were just sampled
    temperature = shtc3.readTemperature()
    humidity = shtc3.readHumidity()

    # Print out the read values
    print("Temperature: {:.2f} C".format(temperature))
    print("Humidity: {:.2f} %\n".format(humidity))

    # Pause for 5 seconds
    time.sleep(5.0)
