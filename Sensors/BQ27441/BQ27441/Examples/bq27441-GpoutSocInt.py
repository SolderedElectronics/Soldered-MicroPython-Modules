# FILE: bq27441-GpoutSocInt.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Demonstrates how to use the BQ27441's SOC_INT function on GPOUT.
#        In this mode GPOUT will pulse every time the state-of-charge (SoC)
#        goes up or down by a set percentage interval.
#
#        NOTE: It is IMPORTANT to connect the battery because this module gets
#        power from the battery and will not work without it!
# WORKS WITH: Fuel gauge BQ27441 breakout: solde.red/333065
# LAST UPDATED: 2026-05-06

from machine import I2C, Pin
import time
from bq27441 import BQ27441, AVG, FULL, REMAIN, SOC_INT

# Set BATTERY_CAPACITY to the design capacity of your battery in mAh
BATTERY_CAPACITY = 600

# Pin connected to BQ27441's GPOUT pin
GPOUT_PIN = 2

# Percentage change interval that triggers a GPOUT pulse
PERCENTAGE_INTERVAL = 1

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
    lipo.setGPOUTFunction(SOC_INT)  # Set GPOUT to SOC_INT mode
    lipo.setSOCIDelta(PERCENTAGE_INTERVAL)  # Set percentage change interval
    lipo.exitConfig()  # Exit config mode to save changes

    # Read back from the chip to confirm the changes
    if lipo.GPOUTPolarity():
        print("GPOUT set to active-HIGH")
    else:
        print("GPOUT set to active-LOW")

    if lipo.GPOUTFunction():
        print("GPOUT function set to BAT_LOW")
    else:
        print("GPOUT function set to SOC_INT")

    print("SOCI Delta: {}".format(lipo.sociDelta()))
    print()

    # Use lipo.pulseGPOUT() to trigger a test pulse on GPOUT.
    # This only works in SOC_INT mode.
    print("Testing GPOUT Pulse")
    lipo.pulseGPOUT()

    timeout = 10000  # The pulse can take a while — max 10 seconds
    while gpout.value() and timeout > 0:
        time.sleep_ms(1)
        timeout -= 1

    if timeout > 0:
        print("GPOUT test successful! ({} ms)".format(10000 - timeout))
        print("GPOUT will pulse whenever the SoC value changes by SOCI delta.")
        print(
            "Or when the battery changes from charging to discharging, or vice-versa."
        )
        print()
    else:
        print("GPOUT didn't pulse.")
        print("Make sure it's connected to pin {} and reset.".format(GPOUT_PIN))
        while True:
            pass


def print_battery_stats():
    soc = lipo.soc()  # Read state-of-charge (%)
    volts = lipo.voltage()  # Read battery voltage (mV)
    current = lipo.current(AVG)  # Read average current (mA)
    full_cap = lipo.capacity(FULL)  # Read full capacity (mAh)
    capacity = lipo.capacity(REMAIN)  # Read remaining capacity (mAh)
    pwr = lipo.power()  # Read average power draw (mW)
    health = lipo.soh()  # Read state-of-health (%)

    print(
        "[{}] {}% | {} mV | {} mA | {}/{} mAh | {} mW | {}%".format(
            time.ticks_ms() // 1000,
            soc,
            volts,
            current,
            capacity,
            full_cap,
            pwr,
            health,
        )
    )


# Run setup
setup_bq27441()

# Main loop — print stats whenever GPOUT pulses (SOC_INT triggered)
while True:
    if gpout.value() == 0:  # GPOUT is active-low
        print_battery_stats()
