# FILE: bmp388-forcedModeWithInterrupt.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Forced mode example using data-ready polling
# WORKS WITH: Pressure & Temperature sensor BMP388 Breakout: www.solde.red/333316
# LAST UPDATED: 2025-01-15

from machine import Pin, I2C
from bmp388 import BMP388
import time

dataReady = False


def interruptHandler(pin):
    global dataReady
    dataReady = True


# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# bmp388 = BMP388(i2c)

# Initialize sensor over Qwiic
bmp388 = BMP388()

# Set sea level pressure for accurate altitude readings
bmp388.setSeaLevelPressure(1025.0)

# Enable data-ready interrupt
bmp388.enableInterrupt()

# Connect sensor INT pin to GPIO2 (adjust for your board)
intPin = Pin(2, Pin.IN, Pin.PULL_UP)
intPin.irq(trigger=Pin.IRQ_RISING, handler=interruptHandler)

while True:
    # Request a new measurement
    bmp388.startForcedConversion()

    # Wait for interrupt flag
    while not dataReady:
        time.sleep(0.005)

    temperature, pressure, altitude = bmp388.getMeasurements()
    if temperature is not None:
        print("{:.2f}*C   {:.2f}hPa   {:.2f}m".format(temperature, pressure, altitude))

    dataReady = False
