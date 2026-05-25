# FILE: BasicStepperDriver-blocking.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Blocking movement — motor moves to each position before continuing
# WORKS WITH: Basic Stepper Driver: www.solde.red/333250
# LAST UPDATED: 2026-05-25

from BasicStepperDriver import BasicStepper

# 4-wire stepper connected to pins 12, 13, 14, 15
stepper = BasicStepper(BasicStepper.FULL4WIRE, 12, 13, 14, 15)

stepper.setMaxSpeed(200.0)
stepper.setAcceleration(100.0)

while True:
    stepper.runToNewPosition(0)
    stepper.runToNewPosition(500)
    stepper.runToNewPosition(100)
    stepper.runToNewPosition(120)
