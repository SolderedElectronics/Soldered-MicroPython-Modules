"""
SingleShot.py - Take on-demand single-shot measurements with the SCD43.

In single-shot mode the sensor takes one measurement at a time instead of
running continuous periodic measurements. This mode is useful for
power-constrained applications where the sensor can be put to sleep between
readings.

Measurement types available:
  - measureSingleShot():        CO2 + temperature + humidity (~5 s)
  - measureSingleShotRhtOnly(): temperature + humidity only (~50 ms)

After each measurement the sensor returns to idle mode and can be powered
down with powerDown() / woken with wakeUp().

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

# begin() starts periodic measurements by default.
# Stop them to enter idle / single-shot mode.
if not sensor.stopPeriodicMeasurement():
    print("Could not stop periodic measurement. Halting.")
    raise SystemExit

print("SCD43 - Single Shot Measurements")
print("Sensor in idle mode. Ready for single-shot measurements.")

while True:
    # Full measurement: CO2 + temperature + humidity. Blocks ~5 seconds.
    print("\nTriggering full single-shot measurement...")

    if sensor.measureAndReadSingleShot():
        print("CO2 (ppm):      ", sensor.getCO2())
        print("Temperature (C):", round(sensor.getTemperature(), 1))
        print("Humidity (%RH): ", round(sensor.getHumidity(), 1))
    else:
        print("Full measurement failed.")

    # Fast RH + temperature only measurement. Blocks ~50 ms.
    # CO2 value is not updated by this command.
    print("\nTriggering RH + temperature only measurement...")

    if sensor.measureSingleShotRhtOnly():
        # Read the result into the internal cache, then retrieve it.
        if sensor.readMeasurement():
            print("Temperature (C):", round(sensor.getTemperature(), 1))
            print("Humidity (%RH): ", round(sensor.getHumidity(), 1))
    else:
        print("RH-only measurement failed.")

    # Optional: power down the sensor between measurements to save energy.
    # sensor.powerDown()
    # ... do other work or sleep ...
    # sensor.wakeUp()

    time.sleep_ms(2000)
