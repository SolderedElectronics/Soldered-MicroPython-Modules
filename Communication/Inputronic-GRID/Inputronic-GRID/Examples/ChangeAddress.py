# FILE: ChangeAddress.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Example showing how to change the I2C address of the Inputronic GRID.
#        Sends a new I2C address to the device. The firmware validates the address,
#        stores it in EEPROM, and re-initializes on the new address — no reset required.
#        The address is retained across power cycles.
#        To restore the default address (0x30), call setAddress(0x30) while
#        connected on whatever address the device currently uses.
# WORKS WITH: Inputronic GRID: www.soldered.com
# LAST UPDATED: 2026-05-12

from machine import I2C, Pin
from InputronicGrid import InputronicGrid
import time

# ── Configuration ─────────────────────────────────────────────────────────────
# Current address the device is on (change if you already moved it)
CURRENT_ADDRESS = 0x30

# New address to assign (must be a valid 7-bit I2C address: 0x08-0x77)
NEW_ADDRESS = 0x31
# ─────────────────────────────────────────────────────────────────────────────

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
grid = InputronicGrid(i2c=i2c, address=CURRENT_ADDRESS)

print("Device found at 0x{:02X}. Changing address to 0x{:02X} ...".format(
    CURRENT_ADDRESS, NEW_ADDRESS))

grid.setAddress(NEW_ADDRESS)

# Give the firmware time to apply the change
time.sleep_ms(50)

# Probe device on new address
try:
    i2c.writeto(NEW_ADDRESS, b"")
    print("Success! Device now at 0x{:02X}".format(NEW_ADDRESS))
    grid.clearLEDs()
except OSError:
    print("Device not found on new address. Re-flash firmware and try again.")
