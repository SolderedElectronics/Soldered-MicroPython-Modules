# FILE: BasicStepperDriver-quickstop.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Demonstrates stop() — decelerates as fast as possible mid-motion
# WORKS WITH: Basic Stepper Driver: www.solde.red/333250
# LAST UPDATED: 2026-05-25

from BasicStepperDriver import BasicStepper

# 4-wire stepper connected to pins 12, 13, 14, 15
stepper = BasicStepper(BasicStepper.FULL4WIRE, 12, 13, 14, 15)

stepper.setMaxSpeed(500)
stepper.setAcceleration(100)

while True:
    stepper.moveTo(500)
    while stepper.currentPosition() != 300:  # Full speed to 300
        stepper.run()
    stepper.stop()          # Decelerate to stop as fast as possible
    stepper.runToPosition() # Complete the deceleration

    stepper.moveTo(-500)
    while stepper.currentPosition() != 0:    # Full speed back to 0
        stepper.run()
    stepper.stop()
    stepper.runToPosition()
