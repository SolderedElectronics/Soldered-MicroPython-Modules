"""
PersistSettings.py - Save sensor configuration to EEPROM so it survives power cycles.

By default, settings such as temperature offset, sensor altitude, and ASC
enable/disable state are stored in RAM only and reset to their defaults
whenever the sensor is powered off. Calling persistSettings() writes the
current configuration to the sensor's internal EEPROM.

The EEPROM is rated for at least 2000 write cycles. Only call persistSettings()
after a configuration change — never in a loop.

Hardware connections:
  - Connect the SCD43 breakout to your board via the Qwiic / I2C connector.
"""

from machine import I2C, Pin
import time
from scd43 import SCD43

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = SCD43()

print("SCD43 - Persist Settings")

if not sensor.begin(i2c):
    print("Sensor not found. Check wiring. Halting.")
    raise SystemExit

# Configuration changes require idle mode.
if not sensor.stopPeriodicMeasurement():
    print("Could not stop periodic measurement. Halting.")
    raise SystemExit

# Apply desired configuration.
sensor.setTemperatureOffset(4.0)               # degrees Celsius
sensor.setSensorAltitude(0)                    # metres above sea level
sensor.setAutomaticSelfCalibrationEnabled(True)
sensor.setAutomaticSelfCalibrationTarget(400)  # ppm (outdoor fresh air)

print("Configuration applied.")

# Write the configuration to EEPROM.
# This call blocks for ~800 ms.
if sensor.persistSettings():
    print("Settings saved to EEPROM. They will persist after power cycle.")
else:
    print("Failed to save settings.")

# Resume periodic measurements.
if not sensor.startPeriodicMeasurement():
    print("Could not restart periodic measurement. Halting.")
    raise SystemExit

while True:
    if sensor.readMeasurement():
        print()
        print("CO2 (ppm):      ", sensor.getCO2())
        print("Temperature (C):", round(sensor.getTemperature(), 1))
        print("Humidity (%RH): ", round(sensor.getHumidity(), 1))
    else:
        print(".", end="")

    time.sleep_ms(500)
