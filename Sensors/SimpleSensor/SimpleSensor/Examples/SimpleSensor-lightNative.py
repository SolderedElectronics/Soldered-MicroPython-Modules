# FILE: SimpleSensor-lightNative.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Simple Light Sensor example using native GPIO/ADC mode
# WORKS WITH: Simple Light Sensor: www.solde.red/333012
# LAST UPDATED: 2026-05-25

from SimpleLightSensor import SimpleLightSensor
import time

# Initialize sensor in native mode
# analog_pin: connect sensor AO pin to an ADC-capable GPIO
# digital_pin: connect sensor DO pin to any GPIO
sensor = SimpleLightSensor(analog_pin=34, digital_pin=35)

# Optional: adjust threshold percentage (default 50%)
# Threshold only affects getValue()-based detection, not the digital pin
# sensor.setThreshold(30.0)

# Calibration: expose sensor to maximum light level, note the getValue() reading,
# then call calibrate() with that value to rescale readings to 0-100%
# sensor.calibrate(90.0)

while True:
    raw = sensor.getRawReading()
    resistance = sensor.getResistance()
    value = sensor.getValue()
    light = sensor.isLightDetected()

    print("Raw: {:4d}  Resistance: {:8.1f} Ohm  Light%: {:6.2f}%  Light detected: {}".format(
        raw, resistance, value, light))
    time.sleep(1)
