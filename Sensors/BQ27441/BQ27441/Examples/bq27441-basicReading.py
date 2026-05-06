# FILE: ReadBatteryStats.py
# AUTHOR: Ported to MicroPython from Arduino example by Robert Peric @ soldered.com
# BRIEF: Basic example showing how to read all battery stats from the BQ27441.
#
#        NOTE: It is IMPORTANT to connect the battery because this module gets
#        power from the battery and will not work without it!
# WORKS WITH: Fuel gauge BQ27441 breakout: solde.red/333065
# LAST UPDATED: 2026-05-06

from machine import I2C, Pin
import time
from bq27441 import BQ27441, AVG, FULL, REMAIN, FILTERED

# Set BATTERY_CAPACITY to the design capacity of your battery in mAh
BATTERY_CAPACITY = 1200

# Initialize I2C and the fuel gauge
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
lipo = BQ27441(i2c)

# Use lipo.begin() to initialize the BQ27441-G1A and confirm
# that it's connected and communicating.
if not lipo.begin():
    print("Error: Unable to communicate with BQ27441.")
    print("  Check wiring and try again.")
    print("  (Battery must be plugged into Fuel Gauge!)")
    while True:
        pass

print("Connected to BQ27441!")

# Set the battery design capacity
lipo.enterConfig()
lipo.setCapacity(BATTERY_CAPACITY)
lipo.exitConfig()


def print_battery_stats():
    soc      = lipo.soc(FILTERED)    # Read state-of-charge (%)
    volts    = lipo.voltage()         # Read battery voltage (mV)
    current  = lipo.current(AVG)     # Read average current (mA)
    full_cap = lipo.capacity(FULL)   # Read full capacity (mAh)
    capacity = lipo.capacity(REMAIN) # Read remaining capacity (mAh)
    pwr      = lipo.power()           # Read average power draw (mW)
    health   = lipo.soh()            # Read state-of-health (%)

    print("SOC:      {}%".format(soc))
    print("Voltage:  {} mV".format(volts))
    print("Current:  {} mA".format(current))
    print("Capacity: {} / {} mAh".format(capacity, full_cap))
    print("Power:    {} mW".format(pwr))
    print("Health:   {}%".format(health))
    print()


# Main loop — print battery stats every second
while True:
    print_battery_stats()
    time.sleep(1)