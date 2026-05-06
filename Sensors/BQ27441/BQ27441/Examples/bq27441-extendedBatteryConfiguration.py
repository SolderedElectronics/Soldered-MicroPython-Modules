# FILE: bq27441-extendedBatteryConfiguration.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Shows how the BQ27441-G1 can be used for extended battery configuration,
#        including setting taper rate and terminate voltage.
#
#        NOTE: It is IMPORTANT to connect the battery because this module gets
#        power from the battery and will not work without it!   
# WORKS WITH: Fuel gauge BQ27441 breakout: solde.red/333065
# LAST UPDATED: 2026-05-06

from machine import I2C, Pin
import time
from bq27441 import BQ27441, AVG, FULL, REMAIN

# Set BATTERY_CAPACITY to the design capacity of your battery in mAh
BATTERY_CAPACITY = 600

# Lowest operational voltage in mV
TERMINATE_VOLTAGE = 3000

# Current at which the charger stops charging the battery in mA
TAPER_CURRENT = 60

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
print("Writing gauge config")

# To configure the values below, you must be in config mode
lipo.enterConfig()

# Set the battery capacity
lipo.setCapacity(BATTERY_CAPACITY)

# Taper Rate = Design Capacity / (0.1 * Taper Current)
lipo.setTaperRate(10 * BATTERY_CAPACITY // TAPER_CURRENT)

# Exit config mode to save changes
lipo.exitConfig()


def print_battery_stats():
    soc      = lipo.soc()             # Read state-of-charge (%)
    volts    = lipo.voltage()         # Read battery voltage (mV)
    current  = lipo.current(AVG)     # Read average current (mA)
    full_cap = lipo.capacity(FULL)   # Read full capacity (mAh)
    capacity = lipo.capacity(REMAIN) # Read remaining capacity (mAh)
    pwr      = lipo.power()           # Read average power draw (mW)
    health   = lipo.soh()            # Read state-of-health (%)

    line = "[{}] {}% | {} mV | {} mA | {}/{} mAh | {} mW | {}%".format(
        time.ticks_ms() // 1000, soc, volts, current, capacity, full_cap, pwr, health
    )

    if lipo.chgFlag():   # Fast charging allowed
        line += " CHG"
    if lipo.fcFlag():    # Full charge detected
        line += " FC"
    if lipo.dsgFlag():   # Battery is discharging
        line += " DSG"

    print(line)


# Main loop — print battery stats every second
while True:
    print_battery_stats()
    time.sleep(1)