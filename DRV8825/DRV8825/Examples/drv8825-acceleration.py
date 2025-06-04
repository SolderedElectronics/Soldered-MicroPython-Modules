# FILE: drv8825-acceleration-example.py
# AUTHOR: Soldered
# BRIEF: An example of accelerating stepper motor.
# LAST UPDATED: 2025-05-27

from drv8825 import DRV8825  # Import the DRV8825 motor driver module
from time import sleep  # Import sleep function for timing delays

# Define GPIO pins for motor control
DIR_PIN = 4  # GPIO pin used for direction control
STEP_PIN = 5  # GPIO pin used for step pulses

# Create a DRV8825 motor instance
motor = DRV8825()

# Initialize the motor with the specified DIR and STEP pins
motor.begin(DIR=DIR_PIN, STEP=STEP_PIN)

# Set the number of steps the motor takes per full rotation (usually 200 for a 1.8° stepper motor)
motor.setStepsPerRotation(200)

# Set the length of each step pulse in microseconds
motor.setStepPulseLength(1000)

# Set motor rotation direction to clockwise
motor.setDirection(DRV8825.CLOCK_WISE)

# Enable the motor driver (turns on output)
motor.enable()

print("Accelerating")

# Gradually increase the step frequency (i.e., speed up the motor)
accelerationFactor = 1
while accelerationFactor < 2000:
    motor.step()  # Send a single step pulse to the motor
    sleep(
        1 / accelerationFactor
    )  # Delay inversely proportional to the factor (higher = faster)
    accelerationFactor += 1  # Increase acceleration factor
    print(accelerationFactor)  # Print current acceleration factor

# Gradually decrease the step frequency (i.e., slow down the motor)
while accelerationFactor > 1:
    motor.step()  # Send a single step pulse
    sleep(1 / accelerationFactor)  # Delay increases as acceleration factor decreases
    accelerationFactor -= 1  # Decrease acceleration factor
    print(accelerationFactor)  # Print current acceleration factor
