# FILE: MCP23017-interrupts.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example showing how to configure interrupts on both INTA and INTB
#        ports. For this example you have to make the following connections:
#        INTA/INTB(IO Expander) - GPIO32 (Dasduino board)
#        The IO expander generates the interrupt and the board detects it
# WORKS WITH: IO expander MCP23017 breakout: www.solde.red/333007
# LAST UPDATED: 2025-07-17

from machine import I2C, Pin
from mcp23017 import *
import time

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# mcp = MCP23017(i2c, address=0x27)

# Create MCP23017 instance
mcp = MCP23017()

# Configure which pin will trigger interrupts (using pin 8 in this example)
INTERRUPT_PIN = A7
BUTTON_PIN = A7  # Using pin 8 as our interrupt source
interruptHappened = 0

# Configure the button pin as input with pull-up and interrupt
mcp.pin(
    BUTTON_PIN,
    mode=1,  # input
    pullup=1,  # enable pull-up resistor
    interrupt_enable=1,  # enable interrupt
    interrupt_compare_default=1,  # compare against default value
    default_value=1,
)  # interrupt when pin goes low (button press)

# Configure the MCP23017 interrupt settings
mcp.config(
    interrupt_polarity=1,  # active-high interrupt (set to 0 for active-low)
    interrupt_mirror=1,  # mirror INTA/INTB (both pins show same interrupt)
    interrupt_open_drain=0,  # push-pull output (set to 1 for open-drain)
)

# Set up the physical interrupt pin on the microcontroller
# Connect this to either INTA or INTB pin of the MCP23017
mcp_int_pin = Pin(32, Pin.IN, Pin.PULL_UP)  # Using GPIO23, adjust for your board


# Interrupt Service Routine (ISR)
def mcp_interrupt_handler(pin):
    # Disable interrupts temporarily while we handle this one
    mcp.pin(BUTTON_PIN, interrupt_enable=0)
    # Trigger variable must use keyword global to not be viewed as local
    global interruptHappened
    interruptHappened = 1


# Configure the interrupt handler
mcp_int_pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=mcp_interrupt_handler)

print("Waiting for interrupts...")
print("Press the button connected to pin 8 to trigger an interrupt")

# Main loop doesn't need to do anything until an interrupt happens
while True:
    # Check if interrupt trigger was set to 1
    if interruptHappened == 1:
        # Inform user
        print("Interrupt detected!")
        # Small delay for debouncing
        time.sleep(0.5)
        # Reset trigger
        interruptHappened = 0
        # Re-enable the interrupt
        mcp.pin(BUTTON_PIN, interrupt_enable=1)
    time.sleep(0.01)
