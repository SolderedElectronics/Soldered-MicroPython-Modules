"""
BasicReadings.py - Read CO2 concentration, temperature, and relative humidity
from the SCD43 sensor using periodic measurements.

The SCD43 outputs a new measurement every 5 seconds.
This example polls for fresh data and prints it.

Hardware connections:
  - Connect the SCD43 breakout to your board via the Qwiic / I2C connector.
"""

from machine import I2C, Pin
import time
from scd43 import SCD43

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = SCD43()

if not sensor.begin(i2c):
    print("Sensor not found. Check wiring. Halting.")
    raise SystemExit

print("SCD43 - Basic Readings")
# The SCD43 produces a new reading every 5 seconds.

while True:
    if sensor.readMeasurement():  # returns True when fresh data is available
        print()
        print("CO2 (ppm):      ", sensor.getCO2())
        print("Temperature (C):", round(sensor.getTemperature(), 1))
        print("Humidity (%RH): ", round(sensor.getHumidity(), 1))
    else:
        print(".", end="")

    time.sleep_ms(500)
