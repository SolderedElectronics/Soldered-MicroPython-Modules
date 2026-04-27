# FILE: pcal6416a-interrupts.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Detect pin-change interrupts from the PCAL6416A using the INT output.
#        Connect pushbuttons between pins A0/A1 and GND. Connect the INT pin of
#        the expander to pin D2 on your board.
# WORKS WITH: PCAL6416A IO Expander breakout: www.solde.red/333351
# LAST UPDATED: 2026-04-23

from machine import Pin, I2C
from pcal6416a import PCAL6416A, PCAL6416A_A0, PCAL6416A_A1, INPUT_PULLUP

# If you aren't using the Qwiic connector, manually enter your I2C pins:
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# expander = PCAL6416A(i2c)

# Initialize expander over Qwiic
expander = PCAL6416A()

expander.pinMode(PCAL6416A_A0, INPUT_PULLUP)
expander.pinMode(PCAL6416A_A1, INPUT_PULLUP)

# Enable change-detection interrupt on both pins
expander.setInterrupt(PCAL6416A_A0, True)
expander.setInterrupt(PCAL6416A_A1, True)

int_flag = False


def isr(pin):
    global int_flag
    int_flag = True


# D2 on most boards — adjust if needed
int_pin = Pin(2, Pin.IN, Pin.PULL_UP)
int_pin.irq(trigger=Pin.IRQ_FALLING, handler=isr)

print("Waiting for interrupts on A0 and A1...")

while True:
    if int_flag:
        int_flag = False
        int_reg = expander.getInterrupts()  # Reading clears the status register

        if int_reg & (1 << PCAL6416A_A0):
            state = expander.digitalRead(PCAL6416A_A0)
            print("Interrupt on A0 — pin is now {}".format("HIGH" if state else "LOW"))

        if int_reg & (1 << PCAL6416A_A1):
            state = expander.digitalRead(PCAL6416A_A1)
            print("Interrupt on A1 — pin is now {}".format("HIGH" if state else "LOW"))
