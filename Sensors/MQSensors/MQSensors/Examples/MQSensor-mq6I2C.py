# FILE: MQSensor-mq6I2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: An example showing how to read LPG concentration from the MQ-6 sensor (Qwiic)
# WORKS WITH: MQ-6 gas sensor with Qwiic: www.solde.red/333200
# LAST UPDATED: 2026-04-30

from MQSensor import MQ6  # Import the MQ6 class
import time  # Module used to pause the board
from machine import I2C, Pin

# Create an instance of the MQ6 sensor object (Qwiic mode)
sensor = MQ6()

# You can also define a custom I2C communication and address if needed:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# sensor = MQ6(i2c=i2c, address=0x30)

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
    print("LPG:", sensor.readSensor(), "ppm")
    time.sleep(0.5)
