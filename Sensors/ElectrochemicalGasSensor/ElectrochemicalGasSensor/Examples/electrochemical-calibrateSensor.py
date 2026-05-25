# FILE: electrochemical-calibrateSensor.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Sensor zero-point calibration example.
# WORKS WITH: Electrochemical Gas Sensor Breakout: solde.red/333218
# LAST UPDATED: 2026-05-21

# Connecting diagram:
#
# Electrochemical Gas Sensor    Dasduino
# Qwiic------------------------>Qwiic
# LMPEN------------------------>32 (GPIO pin, required for configuration)

from machine import I2C, Pin
import time
from ElectrochemicalGasSensor import ElectrochemicalGasSensor, SENSOR_O3

# This value is added to the voltage read from the ADC.
# In an environment with 0 of the target gas, the reading after calibration
# should be just barely 0 PPB — adjust this value until that is the case.
CUSTOM_CALIBRATION = 0

# Initialize I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# Custom ADC address (0x49 default) and GPIO pin for LMPEN
sensor = ElectrochemicalGasSensor(SENSOR_O3, i2c, adc_addr=0x49, config_pin=32)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Electrochemical Gas Sensor - Calibration Example")

if not sensor.begin():
    print("ERROR: Can't init the sensor! Check connections!")
    while True:
        time.sleep_ms(100)

# Apply the zero-point calibration offset
sensor.setCustomZeroCalibration(CUSTOM_CALIBRATION)

print("Sensor initialized successfully!")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    reading = sensor.getPPB()

    # O3 is typically measured in PPB
    # Switch to getPPM() if PPM is more relevant for your use case
    print("Sensor reading: {:.5f} PPB".format(reading))

    time.sleep_ms(2500)
