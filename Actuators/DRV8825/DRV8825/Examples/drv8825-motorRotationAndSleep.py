# FILE: drv8825-motorRotationAndSleep.py
# AUTHOR: Josip Šimun Kuči @ Soldered (based on DRV8825 by Rob Tillaart)
# BRIEF: An example of using the DRV8825 stepper driver to control a motor and
#        Stepping it in each direction, after which it goes into sleep
# WORKS WITH: Stepper motor driver DRV8825 board: www.solde.red/333000
# LAST UPDATED: 2025-05-23

from drv8825 import DRV8825
from time import sleep

# Define pin numbers (adjust to match your board setup)
DIR_PIN = 5  # GPIO5
STEP_PIN = 18  # GPIO18
EN_PIN = 19  # GPIO19 (optional)
RST_PIN = 21  # GPIO21 (optional)
SLP_PIN = 22  # GPIO22 (optional)

# The motor should be connected via the B1,B2,A1,A2 pins
# The motor power supply should be connected to the VIN and GND pins and have a
# parallel connected capacitor, reffer to your motors datasheet for more information

# Initialize the driver
motor = DRV8825()
motor.begin(DIR=DIR_PIN, STEP=STEP_PIN, EN=EN_PIN, RST=RST_PIN, SLP=SLP_PIN)

# Configure motor behavior
motor.setStepsPerRotation(200)  # Typical for 1.8° stepper motors
motor.setStepPulseLength(1000)  # Microseconds per step pulse
motor.setDirection(DRV8825.CLOCK_WISE)
motor.enable()

# Step the motor forward 200 steps (one full rotation)
print("Stepping forward...")
for _ in range(200):
    motor.step()
    sleep(0.005)  # 5ms delay between steps

# Change direction and step back
motor.setDirection(DRV8825.COUNTER_CLOCK_WISE)
print("Stepping backward...")
for _ in range(200):
    motor.step()
    sleep(0.005)

# Put the motor to sleep
motor.sleep()
print("Motor is now sleeping.")
