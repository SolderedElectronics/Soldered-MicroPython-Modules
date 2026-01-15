# FILE: bmp388-normalModeWithFifo.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Normal mode example that collects multiple samples
# WORKS WITH: Pressure & Temperature sensor BMP388 Breakout: www.solde.red/333316
# LAST UPDATED: 2025-01-15

from machine import Pin, I2C
from bmp388 import BMP388
from bmp388_constants import TIME_STANDBY_1280MS, FIFO_DATA_READY, FIFO_CONFIG_ERROR
import time

NO_OF_MEASUREMENTS = 10

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# bmp388 = BMP388(i2c)

# Initialize sensor over Qwiic
bmp388 = BMP388()

# Set sea level pressure for accurate altitude readings
bmp388.setSeaLevelPressure(1025.0)

# Set standby time to roughly 1.3 seconds
bmp388.setTimeStandby(TIME_STANDBY_1280MS)

# Enable FIFO and set watermark
bmp388.enableFIFO()
bmp388.setFIFONoOfMeasurements(NO_OF_MEASUREMENTS)

# Start continuous measurement in normal mode
bmp388.startNormalConversion()

print("Please wait for 13 seconds...")

while True:
    status, temperatures, pressures, altitudes, sensorTime = bmp388.getFIFOData()

    if status == FIFO_DATA_READY:
        for i in range(len(temperatures)):
            altitude = altitudes[i] if i < len(altitudes) else 0.0
            print("{}: {:.2f}*C   {:.2f}hPa   {:.2f}m".format(
                i + 1, temperatures[i], pressures[i], altitude
            ))

        print("Sensor Time: {} ms".format(sensorTime))
        print()
        print("Please wait for 13 seconds...")
    elif status == FIFO_CONFIG_ERROR:
        print("FIFO configuration error.")

    time.sleep(0.05)
