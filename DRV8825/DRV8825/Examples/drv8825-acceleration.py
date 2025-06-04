# FILE: drv8825-acceleration-example.py
# AUTHOR: Soldered
# BRIEF: An example of accelerating stepper motor.
# LAST UPDATED: 2025-05-27

from drv8825 import  DRV8825
from time import sleep

DIR_PIN = 4 #GPIO4
STEP_PIN = 5 #GPIO5

motor=DRV8825()
motor.begin(DIR=DIR_PIN, STEP=STEP_PIN)
motor.setStepsPerRotation(200)
motor.setStepPulseLength(1000)
motor.setDirection(DRV8825.CLOCK_WISE)
motor.enable()

print("Accelerating")


accelerationFactor=1
while accelerationFactor<2000:
    motor.step()
    sleep(1/accelerationFactor)
    accelerationFactor+=1
    print(accelerationFactor)
    
while accelerationFactor>1:
    motor.step()
    sleep(1/accelerationFactor)
    accelerationFactor-=1
    print(accelerationFactor)