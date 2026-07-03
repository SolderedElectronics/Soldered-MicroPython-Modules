# FILE: MQSensor-mq9AllNative.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: An example showing how to read LPG, CH4 and CO from the MQ-9 sensor (native)
# WORKS WITH: MQ-9 gas sensor breakout: www.solde.red/333203
# LAST UPDATED: 2026-04-30

from MQSensor import MQ9  # Import the MQ9 class
import time  # Module used to pause the board

# Connect the sensor AO pin to an ADC-capable GPIO pin.
# Change ANALOG_PIN to match your wiring.
ANALOG_PIN = 34  # ESP32 default

# Create an instance of the MQ9 sensor object (native mode)
sensor = MQ9(analog_pin=ANALOG_PIN)

# Calibrate the sensor in clean air
# Note: sensor must be pre-heated for ~48h before calibration
# This only needs to run once - you can save R0 and restore it with sensor.setR0()
print("Calibrating, please wait...")
if not sensor.calibrate(10):
    print("Calibration error - check wiring and try again")
    raise SystemExit
print("Calibration done! R0 =", sensor.getR0())

# MQ-9 can measure multiple gases by swapping the regression coefficients:
# Gas  |  a     |  b
# LPG  | 1000.5 | -2.186
# CH4  | 4269.6 | -2.648
# CO   | 599.65 | -2.244

# Infinite loop
while True:
    sensor.update()  # Read voltage from sensor once, reuse for all three gases

    sensor.setA(1000.5)
    sensor.setB(-2.186)
    lpg = sensor.readSensor()

    sensor.setA(4269.6)
    sensor.setB(-2.648)
    ch4 = sensor.readSensor()

    sensor.setA(599.65)
    sensor.setB(-2.244)
    co = sensor.readSensor()

    print("| LPG:", lpg, "ppm | CH4:", ch4, "ppm | CO:", co, "ppm |")
    time.sleep(1)
