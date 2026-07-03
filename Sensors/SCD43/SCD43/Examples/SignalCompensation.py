"""
SignalCompensation.py - Configure temperature offset, sensor altitude, and
ambient pressure compensation on the SCD43.

These three settings allow the sensor to compensate for environmental factors
that affect measurement accuracy:

  - Temperature offset: corrects for heat from nearby components.
  - Sensor altitude:    accounts for lower atmospheric pressure at elevation.
  - Ambient pressure:   overrides altitude with a live pressure reading for
                        more precise compensation.

All three require idle mode; stop periodic measurements before changing them.

Hardware connections:
  - Connect the SCD43 breakout to your board via the Qwiic / I2C connector.
"""

from machine import I2C, Pin
import time
from scd43 import SCD43

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = SCD43()

print("SCD43 - Signal Compensation")

if not sensor.begin(i2c):
    print("Sensor not found. Check wiring. Halting.")
    raise SystemExit

# Configuration requires idle mode.
if not sensor.stopPeriodicMeasurement():
    print("Could not stop periodic measurement. Halting.")
    raise SystemExit

# --- Temperature offset ---
print("Temperature offset before:", round(sensor.getTemperatureOffset(), 2), "C")
sensor.setTemperatureOffset(4.0)  # default is 4 C; adjust for your enclosure
print("Temperature offset after: ", round(sensor.getTemperatureOffset(), 2), "C")

# --- Sensor altitude ---
print("Sensor altitude before:", sensor.getSensorAltitude(), "m")
sensor.setSensorAltitude(150)  # set to your installation altitude in metres
print("Sensor altitude after: ", sensor.getSensorAltitude(), "m")

# --- Ambient pressure (overrides altitude-based compensation) ---
# Provide a live pressure reading from a barometer for best accuracy.
if sensor.setAmbientPressure(101300):  # 101300 Pa = standard sea-level pressure
    print("Ambient pressure set to 101300 Pa.")

# Save the temperature offset and altitude to EEPROM.
# Ambient pressure is not persisted and must be re-set after each power cycle.
if sensor.persistSettings():
    print("Temperature offset and altitude saved to EEPROM.")

# Read and print the serial number while we are in idle mode.
serial = sensor.getSerialNumber()
if serial is not None:
    print("Sensor serial number: 0x{:012X}".format(serial))

# Resume periodic measurements.
if not sensor.startPeriodicMeasurement():
    print("Could not restart periodic measurement. Halting.")
    raise SystemExit

print("Periodic measurements restarted.")

while True:
    if sensor.readMeasurement():
        print()
        print("CO2 (ppm):      ", sensor.getCO2())
        print("Temperature (C):", round(sensor.getTemperature(), 1))
        print("Humidity (%RH): ", round(sensor.getHumidity(), 1))
    else:
        print(".", end="")

    time.sleep_ms(500)
