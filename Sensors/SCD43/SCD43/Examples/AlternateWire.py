"""
AlternateWire.py - Use the SCD43 on a secondary I2C bus.

Some microcontrollers expose multiple hardware I2C peripherals.
Pass the desired I2C instance to sensor.begin() to use a bus other
than the default.

If your board only has one I2C bus, use I2C(0) and adjust the pins.

Hardware connections:
  - Connect the SCD43 breakout to the secondary I2C pins of your board.
"""

from machine import I2C, Pin
import time
from scd43 import SCD43

# Secondary I2C bus — adjust id and pins to match your board
i2c1 = I2C(1, scl=Pin(3), sda=Pin(2))
sensor = SCD43()

print("SCD43 - Alternate I2C Bus")

if not sensor.begin(i2c1):
    print("Sensor not found on secondary I2C bus. Check wiring. Halting.")
    raise SystemExit

print("Sensor initialized on secondary I2C bus.")

while True:
    if sensor.readMeasurement():
        print()
        print("CO2 (ppm):      ", sensor.getCO2())
        print("Temperature (C):", round(sensor.getTemperature(), 1))
        print("Humidity (%RH): ", round(sensor.getHumidity(), 1))
    else:
        print(".", end="")

    time.sleep_ms(500)
