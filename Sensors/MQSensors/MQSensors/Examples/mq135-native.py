# FILE: mq135-native.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: An example showing how to read NH3 concentration from the MQ-135 sensor (native)
# WORKS WITH: MQ-135 gas sensor breakout: www.solde.red/333208
# LAST UPDATED: 2026-04-30

from mqsensor import MQ135  # Import the MQ135 class
import time  # Module used to pause the board

# Connect the sensor AO pin to an ADC-capable GPIO pin.
# Change ANALOG_PIN to match your wiring.
ANALOG_PIN = 34  # ESP32 default

# Create an instance of the MQ135 sensor object (native mode)
sensor = MQ135(analog_pin=ANALOG_PIN)

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
    print("NH3:", sensor.readSensor(), "ppm")
    time.sleep(0.5)
