# FILE: DynamicModel.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read and set the dynamic platform model on a u-blox GNSS module
# LAST UPDATED: 2026-05-22

from machine import I2C, Pin
import time
from gnss_ublox import SolderedGNSS, DYN_MODEL_PORTABLE, DYN_MODEL_PEDESTRIAN, DYN_MODEL_AUTOMOTIVE

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
gnss = SolderedGNSS()

if not gnss.begin(i2c):
    print("u-blox GNSS not detected. Check wiring.")
    raise SystemExit

print("u-blox GNSS ready.\n")

MODEL_NAMES = {
    0: "Portable",
    2: "Stationary",
    3: "Pedestrian",
    4: "Automotive",
    5: "Sea",
    6: "Airborne <1g",
    7: "Airborne <2g",
    8: "Airborne <4g",
    9: "Wrist",
    10: "Bike",
}

current = gnss.getDynamicModel()
print(f"Current dynamic model: {current} ({MODEL_NAMES.get(current, 'Unknown')})")

# Switch to pedestrian model
gnss.setDynamicModel(DYN_MODEL_PEDESTRIAN)
time.sleep_ms(100)

current = gnss.getDynamicModel()
print(f"Updated dynamic model : {current} ({MODEL_NAMES.get(current, 'Unknown')})")

# Restore portable model
gnss.setDynamicModel(DYN_MODEL_PORTABLE)
time.sleep_ms(100)
print("Restored to Portable model.")
