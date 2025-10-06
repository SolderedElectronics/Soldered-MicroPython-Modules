# FILE: RFID-UARTExample.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to configure UART communication for the RFID reader as
# well as detecting a scanned tag and printing its raw data
# WORKS WITH: 125kHz RFID tag reader board: www.solde.red/333154
# LAST UPDATED: 2025-10-06
# Import needed libraries
from rfid import RFID
from machine import I2C, Pin

"""
Create an instance of the RFID object in UART mode
NOTE: Default UART speed is 9600, but communication speed can be changed by changing the position of the DIP
switches on the breakout.

            Switch      1     2     3
            9600        0     0     0
            2400        1     0     0
            4800        0     1     0
            19200       1     1     0
            38400       0     0     1
            57600       1     0     1
            115200      0     1     1
            230400      1     1     1
"""
rfid = RFID(rx_pin=18, tx_pin=19, baud_rate=9600)

# Check if there is a connection to the board
if rfid.checkHW():
    print("RFID Reader detected")

    # If connection was successfull, wait for an ID tag to be sensed
    while True:
        # Check if a tag was sensed
        if rfid.available():
            # If it was, get its ID and raw data
            tag_id = rfid.getId()
            raw_data = rfid.getRaw()
            # Print out the values
            print(f"Tag ID: {tag_id}")
            print("Raw Data: ", end="")
            rfid.printHex64(raw_data)

            # Remove the data and wait for a new tag
            rfid.clear()
else:
    # If there isn't, inform the user and quit program
    print("Couldn't detect RFID reader")
