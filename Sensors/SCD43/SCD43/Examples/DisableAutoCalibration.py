"""
DisableAutoCalibration.py - Disable the SCD43's automatic self-calibration (ASC).

ASC is enabled by default and keeps the sensor accurate over time by assuming
periodic exposure to a known CO2 concentration (400 ppm outdoor fresh air by
default). In controlled environments where the sensor is never exposed to fresh
air, ASC should be disabled to prevent drift.

This example disables ASC, saves the setting to EEPROM so it survives a power
cycle, then resumes periodic measurements.

Hardware connections:
  - Connect the SCD43 breakout to your board via the Qwiic / I2C connector.
"""

from machine import I2C, Pin
import time
from scd43 import SCD43

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = SCD43()

print("SCD43 - Disable Auto Calibration")

if not sensor.begin(i2c):
    print("Sensor not found. Check wiring. Halting.")
    raise SystemExit

# Configuration changes require idle mode — stop periodic measurements first.
if not sensor.stopPeriodicMeasurement():
    print("Could not stop periodic measurement. Halting.")
    raise SystemExit

# Check the current ASC state.
print(
    "ASC enabled before change:",
    "yes" if sensor.getAutomaticSelfCalibrationEnabled() else "no",
)

# Disable ASC.
if not sensor.setAutomaticSelfCalibrationEnabled(False):
    print("Failed to disable ASC.")
else:
    print("ASC disabled successfully.")

# Persist the setting so it survives a power cycle.
# Avoid calling persistSettings() on every boot — the EEPROM has a limited
# write-cycle endurance (~2000 writes).
if not sensor.persistSettings():
    print("Failed to persist settings.")
else:
    print("Settings saved to EEPROM.")

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
