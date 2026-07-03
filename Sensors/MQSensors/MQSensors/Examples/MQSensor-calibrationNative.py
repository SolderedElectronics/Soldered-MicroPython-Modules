# FILE: MQSensor-calibrationNative.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: An example for continuously printing R0 calibration readings (native)
#        Run this in clean air to determine the correct R0 for your sensor.
# WORKS WITH: MQ-135 gas sensor breakout: www.solde.red/333208
# LAST UPDATED: 2026-04-30

from MQSensor import MQ135  # Import the MQ135 class
import time  # Module used to pause the board

# Connect the sensor AO pin to an ADC-capable GPIO pin.
# Change ANALOG_PIN to match your wiring.
ANALOG_PIN = 34  # ESP32 default

# Create an instance of the MQ135 sensor object (native mode)
sensor = MQ135(analog_pin=ANALOG_PIN)

print("MQ135 - Calibration")
print(
    "Note: make sure you are in clean air and the sensor has been pre-heating for ~24 hours"
)
print("Counter | R0 value")

counter = 1

# Continuously print R0 readings - average them manually to get your calibration value
while True:
    sensor.update()
    # Calculate a single R0 reading from clean air
    if sensor._sensor_volt > 0:
        RS_air = (sensor._voltage_res * sensor._RL / sensor._sensor_volt) - sensor._RL
        if RS_air < 0:
            RS_air = 0.0
        r0 = RS_air / sensor._Rs_R0_ratio
        print(counter, "|", r0)
    counter += 1
    time.sleep(0.4)
