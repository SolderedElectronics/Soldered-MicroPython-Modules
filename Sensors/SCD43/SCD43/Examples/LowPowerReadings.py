"""
LowPowerReadings.py - Read CO2, temperature, and humidity using the SCD43's
low-power periodic measurement mode.

In low-power mode the sensor updates approximately every 30 seconds instead
of every 5 seconds, significantly reducing average current consumption —
useful for battery-powered devices.

Hardware connections:
  - Connect the SCD43 breakout to your board via the Qwiic / I2C connector.
"""

from machine import I2C, Pin
import time
from scd43 import SCD43

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = SCD43()

print("SCD43 - Low Power Readings")

if not sensor.begin(i2c):
    print("Sensor not found. Check wiring. Halting.")
    raise SystemExit

# begin() starts normal periodic measurement by default.
# Switch to low-power mode: stop normal periodic measurement first,
# then start the low-power variant.
if not sensor.stopPeriodicMeasurement():
    print("Could not stop periodic measurement. Halting.")
    raise SystemExit

if not sensor.startLowPowerPeriodicMeasurement():
    print("Could not start low-power measurement. Halting.")
    raise SystemExit

print("Low-power mode active. New reading every ~30 seconds.")

while True:
    if sensor.readMeasurement():  # returns True when fresh data is available
        print()
        print("CO2 (ppm):      ", sensor.getCO2())
        print("Temperature (C):", round(sensor.getTemperature(), 1))
        print("Humidity (%RH): ", round(sensor.getHumidity(), 1))
    else:
        print(".", end="")

    time.sleep_ms(1000)
