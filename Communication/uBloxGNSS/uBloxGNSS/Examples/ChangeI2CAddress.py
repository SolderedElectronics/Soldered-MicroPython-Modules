# FILE: ChangeI2CAddress.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Change the I2C address of a u-blox GNSS module and reconnect
# LAST UPDATED: 2026-05-22

from machine import I2C, Pin
import time
from gnss_ublox import SolderedGNSS

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
gnss = SolderedGNSS()

OLD_ADDR = 0x42
NEW_ADDR = 0x43

if not gnss.begin(i2c, addr=OLD_ADDR):
    print(f"u-blox GNSS not found at 0x{OLD_ADDR:02X}. Check wiring.")
    raise SystemExit

print(f"Connected at 0x{OLD_ADDR:02X}.")
print(f"Changing I2C address to 0x{NEW_ADDR:02X}...")

if gnss.setI2CAddress(NEW_ADDR):
    print("Address change command sent. Reconnecting...")
    time.sleep_ms(500)

    gnss2 = SolderedGNSS()
    if gnss2.begin(i2c, addr=NEW_ADDR):
        print(f"Successfully reconnected at 0x{NEW_ADDR:02X}.")
        # Restore original address
        gnss2.setI2CAddress(OLD_ADDR)
        print(f"Restored address to 0x{OLD_ADDR:02X}.")
    else:
        print(f"Could not connect at 0x{NEW_ADDR:02X}.")
else:
    print("Failed to send address change command.")
