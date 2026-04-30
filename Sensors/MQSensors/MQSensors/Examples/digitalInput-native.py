# FILE: digitalInput-native.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: An example showing how to use the digital output pin to detect high gas concentration
# WORKS WITH: MQ-135 gas sensor breakout: www.solde.red/333208
# LAST UPDATED: 2026-04-30

from mqsensor import MQ135  # Import the MQ135 class
import time  # Module used to pause the board

# Connect sensor AO to ANALOG_PIN and DO to DIGITAL_PIN.
# Change both pins to match your wiring.
ANALOG_PIN = 34   # ESP32 default
DIGITAL_PIN = 2   # ESP32 default

# Create an instance of the MQ135 sensor with both analog and digital pins
sensor = MQ135(analog_pin=ANALOG_PIN, digital_pin=DIGITAL_PIN)

# Infinite loop
while True:
    if sensor.digitalRead():
        print("Alarm: high concentration detected")
    else:
        print("Status: Normal")
    time.sleep(1)
