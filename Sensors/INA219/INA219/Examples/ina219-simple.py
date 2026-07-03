# FILE: ina219-simple.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Simple example reading voltage and current.
# WORKS WITH: Voltage & Current Sensor INA219 Breakout: solde.red/333075
# LAST UPDATED: 2026-05-06

from machine import I2C, Pin
import time
from ina219 import *

# Initialize I2C and the INA219
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
ina = INA219(i2c)


def check_config():
    """Print the current INA219 configuration to the serial terminal."""

    print("Mode:                 ", end="")
    mode = ina.getMode()
    if mode == INA219_MODE_POWER_DOWN:
        print("Power-Down")
    elif mode == INA219_MODE_SHUNT_TRIG:
        print("Shunt Voltage, Triggered")
    elif mode == INA219_MODE_BUS_TRIG:
        print("Bus Voltage, Triggered")
    elif mode == INA219_MODE_SHUNT_BUS_TRIG:
        print("Shunt and Bus, Triggered")
    elif mode == INA219_MODE_ADC_OFF:
        print("ADC Off")
    elif mode == INA219_MODE_SHUNT_CONT:
        print("Shunt Voltage, Continuous")
    elif mode == INA219_MODE_BUS_CONT:
        print("Bus Voltage, Continuous")
    elif mode == INA219_MODE_SHUNT_BUS_CONT:
        print("Shunt and Bus, Continuous")
    else:
        print("unknown")

    print("Range:                ", end="")
    rng = ina.getRange()
    if rng == INA219_RANGE_16V:
        print("16V")
    elif rng == INA219_RANGE_32V:
        print("32V")
    else:
        print("unknown")

    print("Gain:                 ", end="")
    gain = ina.getGain()
    if gain == INA219_GAIN_40MV:
        print("+/- 40mV")
    elif gain == INA219_GAIN_80MV:
        print("+/- 80mV")
    elif gain == INA219_GAIN_160MV:
        print("+/- 160mV")
    elif gain == INA219_GAIN_320MV:
        print("+/- 320mV")
    else:
        print("unknown")

    print("Bus resolution:       ", end="")
    bus_res = ina.getBusRes()
    if bus_res == INA219_BUS_RES_9BIT:
        print("9-bit")
    elif bus_res == INA219_BUS_RES_10BIT:
        print("10-bit")
    elif bus_res == INA219_BUS_RES_11BIT:
        print("11-bit")
    elif bus_res == INA219_BUS_RES_12BIT:
        print("12-bit")
    else:
        print("unknown")

    print("Shunt resolution:     ", end="")
    shunt_res = ina.getShuntRes()
    if shunt_res == INA219_SHUNT_RES_9BIT_1S:
        print("9-bit / 1 sample")
    elif shunt_res == INA219_SHUNT_RES_10BIT_1S:
        print("10-bit / 1 sample")
    elif shunt_res == INA219_SHUNT_RES_11BIT_1S:
        print("11-bit / 1 sample")
    elif shunt_res == INA219_SHUNT_RES_12BIT_1S:
        print("12-bit / 1 sample")
    elif shunt_res == INA219_SHUNT_RES_12BIT_2S:
        print("12-bit / 2 samples")
    elif shunt_res == INA219_SHUNT_RES_12BIT_4S:
        print("12-bit / 4 samples")
    elif shunt_res == INA219_SHUNT_RES_12BIT_8S:
        print("12-bit / 8 samples")
    elif shunt_res == INA219_SHUNT_RES_12BIT_16S:
        print("12-bit / 16 samples")
    elif shunt_res == INA219_SHUNT_RES_12BIT_32S:
        print("12-bit / 32 samples")
    elif shunt_res == INA219_SHUNT_RES_12BIT_64S:
        print("12-bit / 64 samples")
    elif shunt_res == INA219_SHUNT_RES_12BIT_128S:
        print("12-bit / 128 samples")
    else:
        print("unknown")

    print("Max possible current: {:.5f} A".format(ina.getMaxPossibleCurrent()))
    print("Max current:          {:.5f} A".format(ina.getMaxCurrent()))
    print("Max shunt voltage:    {:.5f} V".format(ina.getMaxShuntVoltage()))
    print("Max power:            {:.5f} W".format(ina.getMaxPower()))


# -------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------
print("Initialize INA219")
print("-----------------------------------------------")

# Default INA219 address is 0x40
if not ina.begin():
    print("Error: Unable to communicate with INA219.")
    print("  Check wiring and try again.")
    while True:
        pass

# Configure INA219
ina.configure(
    INA219_RANGE_32V, INA219_GAIN_320MV, INA219_BUS_RES_12BIT, INA219_SHUNT_RES_12BIT_1S
)

# Calibrate INA219 — Rshunt = 0.1 Ohm, max expected current = 2 A
ina.calibrate(0.1, 2)

# Display configuration
check_config()

print("-----------------------------------------------")

# -------------------------------------------------------------------------
# Main loop
# -------------------------------------------------------------------------
while True:
    print("Bus voltage:   {:.5f} V".format(ina.readBusVoltage()))
    print("Bus power:     {:.5f} W".format(ina.readBusPower()))
    print("Shunt voltage: {:.5f} V".format(ina.readShuntVoltage()))
    print("Shunt current: {:.5f} A".format(ina.readShuntCurrent()))
    print()
    time.sleep(1)
