# FILE: BasicStepperDriver-overshoot.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Demonstrates overshoot handling — motor accelerates past intermediate point then corrects
# WORKS WITH: Basic Stepper Driver: www.solde.red/333250
# LAST UPDATED: 2026-05-25

from BasicStepperDriver import BasicStepper

# 4-wire stepper connected to pins 12, 13, 14, 15
stepper = BasicStepper(BasicStepper.FULL4WIRE, 12, 13, 14, 15)

stepper.setMaxSpeed(150)
stepper.setAcceleration(100)

while True:
    stepper.moveTo(500)
    while stepper.currentPosition() != 300:  # Run at full speed to position 300
        stepper.run()
    stepper.runToNewPosition(0)              # Overshoot then back to 0
