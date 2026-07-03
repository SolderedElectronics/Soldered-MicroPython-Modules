# FILE: MQSensor-mq135I2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: An example showing how to read NH3 concentration from the MQ-135 sensor (Qwiic)
# WORKS WITH: MQ-135 gas sensor with Qwiic: www.solde.red/333208
# LAST UPDATED: 2026-04-30

from MQSensor import MQ135  # Import the MQ135 class
import time  # Module used to pause the board
from machine import I2C, Pin

# Create an instance of the MQ135 sensor object (Qwiic mode)
sensor = MQ135()

# You can also define a custom I2C communication and address if needed:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# sensor = MQ135(i2c=i2c, address=0x30)

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
