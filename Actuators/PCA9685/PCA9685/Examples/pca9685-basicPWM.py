# FILE: pca9685-basicPWM.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Ramp raw PWM duty cycle on channel 0 of the PCA9685
# LAST UPDATED: 2026-07-24

from pca9685 import PCA9685
from utime import sleep_ms

pwm = PCA9685()
pwm.setPWMFreq(1000)  # fast PWM for LEDs/general outputs, not servos

while True:
    for duty in range(0, 4096, 32):
        pwm.setPWM(0, 0, duty)
        sleep_ms(20)
