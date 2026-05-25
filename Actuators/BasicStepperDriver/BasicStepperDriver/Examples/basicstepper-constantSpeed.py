# FILE: basicstepper-constantSpeed.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Constant speed stepper motor control — no acceleration
# WORKS WITH: Basic Stepper Driver: www.solde.red/333250
# LAST UPDATED: 2026-05-25

from basicStepper import BasicStepper

# 4-wire stepper connected to pins 12, 13, 14, 15
stepper = BasicStepper(BasicStepper.FULL4WIRE, 12, 13, 14, 15)

stepper.setMaxSpeed(1000)
stepper.setSpeed(400)    # steps/second, positive = CW

while True:
    stepper.runSpeed()
