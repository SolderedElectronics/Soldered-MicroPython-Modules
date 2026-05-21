# FILE: electrochemical-averagedMeasurement.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Averaged PPM reading example using the built-in averaging function.
# WORKS WITH: Electrochemical Gas Sensor Breakout: solde.red/333218
# LAST UPDATED: 2026-05-21

# Connecting diagram:
#
# Electrochemical Gas Sensor    Dasduino
# Qwiic------------------------>Qwiic
# LMPEN------------------------>GND or GPIO pin (see config_pin parameter below)

from machine import I2C, Pin
import time
from electrochemical_gas_sensor import ElectrochemicalGasSensor, SENSOR_O3

# How many readings to average and how many seconds to wait between them
NUM_READINGS          = 5
SECS_BETWEEN_READINGS = 3

# Initialize I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))

# Create sensor object - change SENSOR_O3 to match your sensor type
# Available types: SENSOR_CO, SENSOR_NO2, SENSOR_SO2, SENSOR_O3,
#                  SENSOR_NO, SENSOR_H2S, SENSOR_NH3, SENSOR_CL2
sensor = ElectrochemicalGasSensor(SENSOR_O3, i2c)

# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Electrochemical Gas Sensor - Averaged Measurement Example")

if not sensor.begin():
    print("ERROR: Can't init the sensor! Check connections!")
    while True:
        time.sleep_ms(100)

print("Sensor initialized successfully!")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    # getAveragedPPM is a blocking call — it waits between each reading
    reading = sensor.getAveragedPPB(NUM_READINGS, SECS_BETWEEN_READINGS)

    # If PPM is more relevant for your sensor, use:
    # reading = sensor.getAveragedPPM(NUM_READINGS, SECS_BETWEEN_READINGS)

    print("Sensor reading: {:.5f} PPB".format(reading))

    time.sleep_ms(2500)
