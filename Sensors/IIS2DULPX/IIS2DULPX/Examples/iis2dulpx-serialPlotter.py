# FILE: iis2dulpx-serialPlotter.py
# AUTHOR: Josip Simun Kuci @ Soldered
# BRIEF: Poll IIS2DULPX acceleration values for serial plotting
# WORKS WITH: IIS2DULPX Accelerometer breakout: www.solde.red/333363
# LAST UPDATED: 2026-04-24

from machine import I2C, Pin
from iis2dulpx import IIS2DULPX, IIS2DULPX_OK
import time

# If you are not using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# sensor = IIS2DULPX(i2c)

sensor = IIS2DULPX()

if sensor.begin() != IIS2DULPX_OK:
    raise Exception("Failed to initialize IIS2DULPX sensor")

if sensor.Enable_X() != IIS2DULPX_OK:
    raise Exception("Failed to enable accelerometer")

print("IIS2DULPX sensor initialized and accelerometer enabled.")

while True:
    x, y, z = sensor.Get_X_Axes()
    print("Accel-X [mg]:{},Accel-Y[mg]:{},Accel-Z[mg]:{}".format(x, y, z))
    time.sleep_ms(50)
