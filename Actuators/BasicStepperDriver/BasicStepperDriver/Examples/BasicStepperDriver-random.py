# FILE: BasicStepperDriver-random.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Random speed, acceleration and target position — motor keeps changing behaviour
# WORKS WITH: Basic Stepper Driver: www.solde.red/333250
# LAST UPDATED: 2026-05-25

from BasicStepperDriver import BasicStepper
import time
import random

# 4-wire stepper connected to pins 12, 13, 14, 15
stepper = BasicStepper(BasicStepper.FULL4WIRE, 12, 13, 14, 15)

while True:
    if stepper.distanceToGo() == 0:
        time.sleep_ms(1000)
        stepper.moveTo(random.randint(0, 199))
        stepper.setMaxSpeed(random.randint(1, 200))
        stepper.setAcceleration(random.randint(1, 200))

    stepper.run()
