# FILE: MCP23017-portConfigMethods.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example showing how to configure specific pins as input or output using 
#        the method approach, more information available here:  
#        https://github.com/mcauser/micropython-mcp23017/tree/master/examples/interfaces
# WORKS WITH: IO expander MCP23017 breakout: www.solde.red/333007
# LAST UPDATED: 2025-07-17 

from machine import I2C, Pin
from mcp23017 import *
from time import sleep

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# mcp = MCP23017(i2c, address=0x27)

# Pins range from A0 - A7 and B0 - B7
# Set variables to hold pin values
ledPin=A0

buttonPin=B1

# Create MCP23017 instance with default address 0x27
mcp = MCP23017()

# Configure the button pin to an input_pullup configuration
mcp.pin(buttonPin,mode=INPUT_PULLUP)



# Infinite loop
while True:
    # If the button is pressed, turn on the LED
    if(mcp.pin(buttonPin)==LOW):
        mcp.pin(pin=ledPin, mode=OUTPUT, value=HIGH)
    # Else it stays off
    else: 
        mcp.pin(pin=ledPin, mode=OUTPUT, value=LOW)