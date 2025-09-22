# FILE: tmp117-simpleRead.py 
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  Example showing how to take a simple temperature
#         measurement every 100ms in Celsius
# WORKS WITH: Temperature Sensor TMP117 Breakout: www.solde.red/333175
# LAST UPDATED: 2025-09-22 

from machine import I2C, Pin
import tmp117
import time

# Initialize I2C
i2c = I2C()

# Create TMP117 instance
sensor = tmp117.TMP117(i2c, addr=0x49)

# Initialize with default settings
sensor.init()

# Infinite loop
while True:
    # Update sensor register values and check for new measurements
    sensor.update()
    # Read temperature
    temperature = sensor.getTemperature()
    print(f"Temperature: {temperature:.2f}°C")
    time.sleep(0.2)