# FILE: mq138-customConfig-native.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: An example showing how to use a custom regression config on the MQ-138 sensor (native)
#        This example measures alcohol instead of the default toluene.
# WORKS WITH: MQ-138 gas sensor breakout: www.solde.red/333207
# LAST UPDATED: 2026-04-30

from mqsensor import MQ138, REGRESSION_LINEAR  # Import MQ138 and regression constant
import time  # Module used to pause the board

# Connect the sensor AO pin to an ADC-capable GPIO pin.
# Change ANALOG_PIN to match your wiring.
ANALOG_PIN = 34  # ESP32 default

# Create an instance of the MQ138 sensor object (native mode)
sensor = MQ138(analog_pin=ANALOG_PIN)

# Override the regression model to measure alcohol instead of the default toluene
# MQ-138 regression coefficients:
# Gas      |  a       |  b
# Alcohol  | -0.46099 |  0.0681
# Acetone  | -0.52356 |  0.49225
# Toluene  | -0.4434  |  0.15397
sensor.setRegressionModel(REGRESSION_LINEAR, -0.46099, 0.0681)

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
    print("Alcohol:", sensor.readSensor(), "ppm")
    time.sleep(0.5)
