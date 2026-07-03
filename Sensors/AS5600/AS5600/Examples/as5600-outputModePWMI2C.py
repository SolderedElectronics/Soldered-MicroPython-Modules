# FILE: as5600-outputModePWMI2C.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Set AS5600 to output a PWM signal on OUT, and measure the pulse width directly
# WORKS WITH: Position sensor AS5600 breakout: solde.red/333183
# LAST UPDATED: 2026-07-02

from as5600 import AS5600, OUTMODE_PWM, PWM_920
from machine import Pin, time_pulse_us
import time

# Connect AS5600 OUT pin to PWM_PIN
# Make sure the pin supports pulse timing and isn't used for SCL/SDA or something else
PWM_PIN = 16

sensor = AS5600()  # Raises Exception if the sensor isn't found

while not sensor.magnetDetected():
    print("Magnet not detected!")
    time.sleep(1)

sensor.setOutputMode(OUTMODE_PWM)
sensor.setPWMFrequency(PWM_920)  # PWM_115 / PWM_230 / PWM_460 / PWM_920 Hz

pwmPin = Pin(PWM_PIN, Pin.IN)

while True:
    print("Angle: {}".format(sensor.readAngle()))
    print("PWM reading (us): {}".format(time_pulse_us(pwmPin, 1)))

    time.sleep(1)
