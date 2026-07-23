# FILE: electrochemical-bridgeBoard.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Single sensor PPM reading example for the ATtiny404 bridge board revision,
#        which allows daisy-chaining multiple boards on one I2C bus.
# WORKS WITH: Electrochemical Gas Sensor Breakout: solde.red/333218
# LAST UPDATED: 2026-07-23

# Connecting diagram:
#
# Electrochemical Gas Sensor    Dasduino
# Qwiic------------------------>Qwiic
#
# Note: on this board revision, LMPEN is hardwired to GND, so there's no
# config_pin to set - it's ignored whenever adc_addr falls in the bridge
# range (0x30-0x37). Set the desired address using the jumpers on the back
# of the board before powering it on.

from machine import I2C, Pin
import time
from ElectrochemicalGasSensor import ElectrochemicalGasSensor, SENSOR_O3

# Initialize I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# Create sensor object, addressed via the ATtiny bridge's easyC jumpers
# (address = 0x30 + jumper offset, giving a range of 0x30-0x37).
# Any additional boards on the same bus just need a different jumper
# setting, same as twoSensors.py does for legacy boards with 0x49/0x4A/0x4B.
sensor = ElectrochemicalGasSensor(SENSOR_O3, i2c, adc_addr=0x30)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Electrochemical Gas Sensor - ATtiny Bridge Board Example")

if not sensor.begin():
    print("ERROR: Can't init the sensor! Check connections and jumper address!")
    while True:
        time.sleep_ms(100)

print("Sensor initialized successfully!")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    reading = sensor.getPPM()

    # If PPB is more relevant for your sensor, use:
    # reading = sensor.getPPB()

    print("Sensor reading: {:.5f} PPM".format(reading))

    time.sleep_ms(2500)
