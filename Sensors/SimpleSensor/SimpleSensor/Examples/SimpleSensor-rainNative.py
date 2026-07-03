# FILE: SimpleSensor-rainNative.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Simple Rain Sensor example using native GPIO/ADC mode
# WORKS WITH: Simple Rain Sensor: www.solde.red/333010
# LAST UPDATED: 2026-05-25

from SimpleRainSensor import SimpleRainSensor
import time

# Initialize sensor in native mode
# analog_pin: connect sensor AO pin to an ADC-capable GPIO
# digital_pin: connect sensor DO pin to any GPIO
sensor = SimpleRainSensor(analog_pin=34, digital_pin=35)

# Optional: adjust threshold percentage (default 50%)
# Threshold only affects getValue()-based detection, not the digital pin
# sensor.setThreshold(60.0)

# Calibration: submerge sensor in water, note the getValue() reading,
# then call calibrate() with that value to rescale readings to 0-100%
# sensor.calibrate(85.0)

while True:
    raw = sensor.getRawReading()
    resistance = sensor.getResistance()
    value = sensor.getValue()
    raining = sensor.isRaining()

    print("Raw: {:4d}  Resistance: {:8.1f} Ohm  Rain%: {:6.2f}%  Raining: {}".format(
        raw, resistance, value, raining))
    time.sleep(1)
