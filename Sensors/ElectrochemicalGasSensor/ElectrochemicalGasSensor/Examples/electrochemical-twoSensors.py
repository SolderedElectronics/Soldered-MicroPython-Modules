# FILE: electrochemical-twoSensors.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Two O3 sensor PPB reading example using two breakouts on one I2C bus.
# WORKS WITH: Electrochemical Gas Sensor Breakout: solde.red/333218
# LAST UPDATED: 2026-05-21

# Connecting diagram:
#
# Sensor 1                      Dasduino
# Qwiic------------------------>Qwiic
# LMPEN------------------------>25 (GPIO pin, required for I2C configuration)
#
# Sensor 2                      Dasduino
# Qwiic------------------------>Qwiic (same bus)
# LMPEN------------------------>32 (GPIO pin, required for I2C configuration)
#
# Set different ADC I2C addresses on each breakout using the address jumpers.
# Both LMP91000 chips share address 0x48 — the LMPEN pin selects which one
# is active during configuration, so a GPIO pin is required for each sensor.

from machine import I2C, Pin
import time
from ElectrochemicalGasSensor import ElectrochemicalGasSensor, SENSOR_O3

# Initialize shared I2C bus
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# Sensor 1: ADC address 0x4A, LMPEN on pin 25
sensor1 = ElectrochemicalGasSensor(SENSOR_O3, i2c, adc_addr=0x4A, config_pin=25)

# Sensor 2: ADC address 0x49, LMPEN on pin 32
sensor2 = ElectrochemicalGasSensor(SENSOR_O3, i2c, adc_addr=0x49, config_pin=32)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Electrochemical Gas Sensor - Two Sensors Example")

if not sensor1.begin():
    print("ERROR: Can't init sensor 1! Check connections!")
    while True:
        time.sleep_ms(100)

print("Sensor 1 initialized successfully!")

if not sensor2.begin():
    print("ERROR: Can't init sensor 2! Check connections!")
    while True:
        time.sleep_ms(100)

print("Sensor 2 initialized successfully!")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    reading1 = sensor1.getPPB()
    reading2 = sensor2.getPPB()

    print("Sensor 1 reading: {:.5f} PPB".format(reading1))
    print("Sensor 2 reading: {:.5f} PPB".format(reading2))

    time.sleep_ms(2500)
