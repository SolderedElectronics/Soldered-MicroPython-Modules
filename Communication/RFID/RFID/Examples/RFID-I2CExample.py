# FILE: RFID-I2CExample.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example showing how to configure I2C communication for the RFID reader as
# well as detecting a scanned tag and printing its raw data
# WORKS WITH: 125kHz RFID tag reader board: www.solde.red/333273
# LAST UPDATED: 2025-10-06
# Import needed libraries
from rfid import RFID
from machine import I2C, Pin

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
rfid = RFID(i2c=i2c, i2c_address=0x30)

if rfid.checkHW():
    print("RFID Reader detected")

    while True:
        if rfid.available():
            tag_id = rfid.getId()
            raw_data = rfid.getRaw()
            print(f"Tag ID: {tag_id}")
            print("Raw Data: ", end="")
            rfid.printHex64(raw_data)
else:
    print("Couldn't detect RFID reader")
