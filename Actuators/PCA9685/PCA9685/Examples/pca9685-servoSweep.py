# FILE: pca9685-servoSweep.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Sweep a hobby servo on channel 0 back and forth using PCA9685
# LAST UPDATED: 2026-07-24

from pca9685 import PCA9685
from utime import sleep_ms

pwm = PCA9685()  # sets 50Hz PWM frequency by default, suitable for hobby servos

# Adjust to match your servo's datasheet if it doesn't reach full range
pwm.setServoPulseRange(500, 2500)  # microseconds
pwm.setServoAngleRange(0, 180)  # degrees

while True:
    for angle in range(0, 181):
        pwm.setServoAngle(0, angle)
        sleep_ms(15)

    for angle in range(180, -1, -1):
        pwm.setServoAngle(0, angle)
        sleep_ms(15)
