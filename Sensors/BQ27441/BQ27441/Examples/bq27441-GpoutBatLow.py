# FILE: bq27441-GpoutBatLow.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Demonstrates how to use the BQ27441's BAT_LOW function on GPOUT.
#        In this mode GPOUT will become active whenever the battery goes
#        below a set threshold.
#
#        NOTE: It is IMPORTANT to connect the battery because this module gets
#        power from the battery and will not work without it!
# WORKS WITH: Fuel gauge BQ27441 breakout: solde.red/333065
# LAST UPDATED: 2026-05-06

from machine import I2C, Pin
import time
from bq27441 import BQ27441, AVG, FULL, REMAIN, BAT_LOW

# Set BATTERY_CAPACITY to the design capacity of your battery in mAh
BATTERY_CAPACITY = 600

SOCI_SET = 15  # Interrupt set threshold at 15%
SOCI_CLR = 20  # Interrupt clear threshold at 20%
SOCF_SET = 5  # Final threshold set at 5%
SOCF_CLR = 10  # Final threshold clear at 10%

# Pin connected to BQ27441's GPOUT pin
GPOUT_PIN = 2

# Initialize I2C and the fuel gauge
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
lipo = BQ27441(i2c)

# Initialize the GPOUT pin as input with pull-up
gpout = Pin(GPOUT_PIN, Pin.IN, Pin.PULL_UP)


def setup_bq27441():
    # Use lipo.begin() to initialize the BQ27441-G1A and confirm
    # that it's connected and communicating.
    if not lipo.begin():
        print("Error: Unable to communicate with BQ27441.")
        print("  Check wiring and try again.")
        print("  (Battery must be plugged into Fuel Gauge!)")
        while True:
            pass

    print("Connected to BQ27441!")

    # In this example we manually enter and exit config mode. By controlling
    # config mode manually, you can set the chip up faster -- completing all
    # of the setup in a single config mode sweep.
    lipo.enterConfig()  # Must be in config mode to set values below
    lipo.setCapacity(BATTERY_CAPACITY)  # Set the battery capacity
    lipo.setGPOUTPolarity(False)  # Set GPOUT to active-low
    lipo.setGPOUTFunction(BAT_LOW)  # Set GPOUT to BAT_LOW mode
    lipo.setSOC1Thresholds(SOCI_SET, SOCI_CLR)  # Set SOCI set and clear thresholds
    lipo.setSOCFThresholds(SOCF_SET, SOCF_CLR)  # Set SOCF set and clear thresholds
    lipo.exitConfig()

    # Read back from the chip to confirm the changes
    if lipo.GPOUTPolarity():
        print("GPOUT set to active-HIGH")
    else:
        print("GPOUT set to active-LOW")

    if lipo.GPOUTFunction():
        print("GPOUT function set to BAT_LOW")
    else:
        print("GPOUT function set to SOC_INT")

    print("SOC1 Set Threshold: {}%".format(lipo.SOC1SetThreshold()))
    print("SOC1 Clear Threshold: {}%".format(lipo.SOC1ClearThreshold()))
    print("SOCF Set Threshold: {}%".format(lipo.SOCFSetThreshold()))
    print("SOCF Clear Threshold: {}%".format(lipo.SOCFClearThreshold()))


def print_battery_stats():
    soc = lipo.soc()  # Read state-of-charge (%)
    volts = lipo.voltage()  # Read battery voltage (mV)
    current = lipo.current(AVG)  # Read average current (mA)
    full_cap = lipo.capacity(FULL)  # Read full capacity (mAh)
    capacity = lipo.capacity(REMAIN)  # Read remaining capacity (mAh)
    pwr = lipo.power()  # Read average power draw (mW)
    health = lipo.soh()  # Read state-of-health (%)

    print(
        "{}% | {} mV | {} mA | {}/{} mAh | {} mW | {}% | flags: 0x{:04X}".format(
            soc, volts, current, capacity, full_cap, pwr, health, lipo.flags()
        )
    )


# Run setup
setup_bq27441()

# Main loop
while True:
    print_battery_stats()

    # GPOUT is active-low — if it goes low, a threshold was crossed
    if not gpout.value():
        if lipo.socfFlag():
            print("<!-- WARNING: Battery Dangerously Low -->")
        elif lipo.socFlag():
            print("<!-- WARNING: Battery Low -->")

    time.sleep(1)
