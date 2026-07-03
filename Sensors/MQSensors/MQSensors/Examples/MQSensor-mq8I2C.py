# FILE: MQSensor-mq8I2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: An example showing how to read H2 concentration from the MQ-8 sensor (Qwiic)
# WORKS WITH: MQ-8 gas sensor with Qwiic: www.solde.red/333202
# LAST UPDATED: 2026-04-30

from MQSensor import MQ8  # Import the MQ8 class
import time  # Module used to pause the board
from machine import I2C, Pin

# Create an instance of the MQ8 sensor object (Qwiic mode)
sensor = MQ8()

# You can also define a custom I2C communication and address if needed:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# sensor = MQ8(i2c=i2c, address=0x30)

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
    print("H2:", sensor.readSensor(), "ppm")
    time.sleep(0.5)
