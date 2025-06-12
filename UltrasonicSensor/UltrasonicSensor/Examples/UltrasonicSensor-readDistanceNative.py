# FILE: UltrasonicSensor-readDistanceNative.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to read the distance of the Native Ultrasonic sensor
# WORKS WITH: Ultrasonic module HC-SR04: www.solde.red/101202
# LAST UPDATED: 2025-06-12

from machine import I2C, Pin
from UltrasonicSensor import UltrasonicSensor
import time

# Create sensor instance
sensor = UltrasonicSensor(trig_pin=2,echo_pin=35)

while True:
    time.sleep(0.1)  # Small delay for measurement

    # The sensor sends a pulse through the trigger pin, which is deflected
    # By a surface in front of it and picked up by the echo pin, we then use the
    # time it took the impulse to reflect to calculate the distance
    distance = sensor.getDistance()

    time.sleep(0.1)  # Small delay for measurement
    # How long did it take for the pulse to reflect
    duration = sensor.getDuration()

    # Print out the distance and duration to the user
    print(f"Distance: {distance:.2f} cm")
    print(f"Time it took: {duration:.2f} us\n")

    time.sleep(0.25)  # Delay between readings
