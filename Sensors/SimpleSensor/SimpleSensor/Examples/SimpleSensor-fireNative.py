# FILE: SimpleSensor-fireNative.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Simple Fire Sensor example using native GPIO/ADC mode
# WORKS WITH: Simple Fire Sensor: www.solde.red/333013
# LAST UPDATED: 2026-05-25

from SimpleFireSensor import SimpleFireSensor
import time

# Initialize sensor in native mode
# analog_pin: connect sensor AO pin to an ADC-capable GPIO
# digital_pin: connect sensor DO pin to any GPIO
sensor = SimpleFireSensor(analog_pin=34, digital_pin=35)

# Optional: adjust threshold percentage (default 50%)
# Threshold only affects getValue()-based detection, not the digital pin
# sensor.setThreshold(40.0)

# Calibration: hold flame at max detection range, note the getValue() reading,
# then call calibrate() with that value to rescale readings to 0-100%
# sensor.calibrate(80.0)

while True:
    raw = sensor.getRawReading()
    resistance = sensor.getResistance()
    value = sensor.getValue()
    fire = sensor.isFireDetected()

    print(
        "Raw: {:4d}  Resistance: {:8.1f} Ohm  Fire%: {:6.2f}%  Fire detected: {}".format(
            raw, resistance, value, fire
        )
    )
    time.sleep(1)
