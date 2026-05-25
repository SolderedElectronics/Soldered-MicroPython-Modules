# FILE: BasicStepperDriver-multipleSteppers.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Three independent stepper motors running simultaneously at different speeds
# WORKS WITH: Basic Stepper Driver: www.solde.red/333250
# LAST UPDATED: 2026-05-25

from BasicStepperDriver import BasicStepper

# Each motor requires its own board and 4 GPIO pins
stepper1 = BasicStepper(BasicStepper.FULL4WIRE, 12, 13, 14, 15)
stepper2 = BasicStepper(BasicStepper.FULL4WIRE, 16, 17, 18, 19)
stepper3 = BasicStepper(BasicStepper.FULL2WIRE, 21, 22)

stepper1.setMaxSpeed(200.0)
stepper1.setAcceleration(100.0)
stepper1.moveTo(24)

stepper2.setMaxSpeed(300.0)
stepper2.setAcceleration(100.0)
stepper2.moveTo(1000000)

stepper3.setMaxSpeed(300.0)
stepper3.setAcceleration(100.0)
stepper3.moveTo(1000000)

while True:
    # Reverse stepper1 when it reaches target
    if stepper1.distanceToGo() == 0:
        stepper1.moveTo(-stepper1.currentPosition())

    # Call run() on each motor every loop iteration
    stepper1.run()
    stepper2.run()
    stepper3.run()
