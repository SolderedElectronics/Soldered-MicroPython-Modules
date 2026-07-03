# FILE: electrochemical-singleSensor.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Single sensor PPM reading example.
# WORKS WITH: Electrochemical Gas Sensor Breakout: solde.red/333218
# LAST UPDATED: 2026-05-21

# Connecting diagram:
#
# Electrochemical Gas Sensor    Dasduino
# Qwiic------------------------>Qwiic
# LMPEN------------------------>GND or GPIO pin (see config_pin parameter below)

from machine import I2C, Pin
import time
from ElectrochemicalGasSensor import ElectrochemicalGasSensor, SENSOR_O3

# Initialize I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# Create sensor object - change SENSOR_O3 to match your sensor type
# Available types: SENSOR_CO, SENSOR_NO2, SENSOR_SO2, SENSOR_O3,
#                  SENSOR_NO, SENSOR_H2S, SENSOR_NH3, SENSOR_CL2
sensor = ElectrochemicalGasSensor(SENSOR_O3, i2c)

# If using a custom ADC address or a GPIO pin for LMP91000 MENB:
# sensor = ElectrochemicalGasSensor(SENSOR_O3, i2c, adc_addr=0x4B, config_pin=5)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Electrochemical Gas Sensor - Single Sensor Example")

if not sensor.begin():
    print("ERROR: Can't init the sensor! Check connections!")
    while True:
        time.sleep_ms(100)

print("Sensor initialized successfully!")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    reading = sensor.getPPB()

    # If PPM is more relevant for your sensor, use:
    # reading = sensor.getPPM()

    print("Sensor reading: {:.5f} PPB".format(reading))

    time.sleep_ms(2500)
