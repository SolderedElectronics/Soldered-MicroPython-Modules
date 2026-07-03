# FILE: SimpleSensor-soilNative.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Simple Soil Humidity Sensor example using native GPIO/ADC mode
# WORKS WITH: Simple Soil Humidity Sensor: www.solde.red/333011
# LAST UPDATED: 2026-05-25

from SimpleSoilSensor import SimpleSoilSensor
import time

# Initialize sensor in native mode
# analog_pin: connect sensor AO pin to an ADC-capable GPIO
# digital_pin: connect sensor DO pin to any GPIO
sensor = SimpleSoilSensor(analog_pin=34, digital_pin=35)

# Optional: adjust threshold percentage (default 50%)
# Threshold only affects getValue()-based detection, not the digital pin
# sensor.setThreshold(40.0)

# Calibration: insert sensor into moist soil, note the getValue() reading,
# then call calibrate() with that value to rescale readings to 0-100%
# sensor.calibrate(85.0)

while True:
    raw = sensor.getRawReading()
    resistance = sensor.getResistance()
    value = sensor.getValue()
    moist = sensor.isMoist()

    print("Raw: {:4d}  Resistance: {:8.1f} Ohm  Moisture%: {:6.2f}%  Moist: {}".format(
        raw, resistance, value, moist))
    time.sleep(1)
