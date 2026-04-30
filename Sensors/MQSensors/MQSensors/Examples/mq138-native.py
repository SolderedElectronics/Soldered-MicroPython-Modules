# FILE: mq138-native.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: An example showing how to read toluene concentration from the MQ-138 sensor (native)
# WORKS WITH: MQ-138 gas sensor breakout: www.solde.red/333207
# LAST UPDATED: 2026-04-30

from mqsensor import MQ138  # Import the MQ138 class
import time  # Module used to pause the board

# Connect the sensor AO pin to an ADC-capable GPIO pin.
# Change ANALOG_PIN to match your wiring.
ANALOG_PIN = 34  # ESP32 default

# Create an instance of the MQ138 sensor object (native mode)
sensor = MQ138(analog_pin=ANALOG_PIN)

# Calibrate the sensor in clean air
# Note: sensor must be pre-heated for ~48h before calibration
# This only needs to run once - you can save R0 and restore it with sensor.setR0()
print("Calibrating, please wait...")
if not sensor.calibrate(10):
    print("Calibration error - check wiring and try again")
    raise SystemExit
print("Calibration done! R0 =", sensor.getR0())

# Infinite loop
while True:
    sensor.update()  # Read voltage from sensor
    print("Toluene:", sensor.readSensor(), "ppm")
    time.sleep(0.5)
