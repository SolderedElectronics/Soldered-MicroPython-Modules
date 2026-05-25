# FILE: basicstepper-bounce.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Bounce between two positions with acceleration and deceleration
# WORKS WITH: Basic Stepper Driver: www.solde.red/333250
# LAST UPDATED: 2026-05-25

from basicStepper import BasicStepper

# 4-wire stepper connected to pins 12, 13, 14, 15
stepper = BasicStepper(BasicStepper.FULL4WIRE, 12, 13, 14, 15)

stepper.setMaxSpeed(100)
stepper.setAcceleration(20)
stepper.moveTo(500)

while True:
    # Reverse direction when target is reached
    if stepper.distanceToGo() == 0:
        stepper.moveTo(-stepper.currentPosition())

    stepper.run()
