# FILE: iis2dulpx-interruptWakeup.py
# AUTHOR: Josip Simun Kuci @ Soldered
# BRIEF: Use IIS2DULPX wake-up interrupt to detect movement
# WORKS WITH: IIS2DULPX Accelerometer breakout: www.solde.red/333363
# LAST UPDATED: 2026-04-24

from machine import Pin, I2C
from iis2dulpx import IIS2DULPX, IIS2DULPX_OK, IIS2DULPX_INT1_PIN
import time

# Hardware setup:
# - Connect breakout INT1 pin to INT1_PIN below
# - Optional: connect a buzzer or LED to ALERT_PIN
INT1_PIN = 5
ALERT_PIN = 23

mems_event = False


def int1_callback(pin):
    global mems_event
    mems_event = True


# If you are not using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# sensor = IIS2DULPX(i2c)

sensor = IIS2DULPX()
alert = Pin(ALERT_PIN, Pin.OUT)
int1 = Pin(INT1_PIN, Pin.IN)
int1.irq(trigger=Pin.IRQ_RISING, handler=int1_callback)

if sensor.begin() != IIS2DULPX_OK:
    raise Exception("Failed to initialize IIS2DULPX sensor")

if sensor.Enable_X() != IIS2DULPX_OK:
    raise Exception("Failed to enable accelerometer")

if sensor.Enable_Wake_Up_Detection(IIS2DULPX_INT1_PIN) != IIS2DULPX_OK:
    raise Exception("Failed to enable wake-up detection")

print("Wake-up detection enabled")

while True:
    if mems_event:
        mems_event = False
        status = sensor.Get_X_Event_Status()
        if status["WakeUpStatus"]:
            print("Wake up Detected!")
            alert.on()
            time.sleep_ms(200)
            alert.off()

    time.sleep_ms(10)
