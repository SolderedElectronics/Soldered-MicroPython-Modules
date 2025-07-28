# FILE: ad8495-measureTemperature&Voltage.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:
# LAST UPDATED: 2025-07-02

from ad8495 import AD8495
from time import sleep

# Initialize the sensor on GPIO 32
# ESP32 ADCs typically default to 12-bit (0–4095)
# Reference voltage is usually 3.3V
sensor = AD8495(pin=32, resolution_bits=12, reference_voltage=3.3)

# Optional: apply a temperature offset for calibration
# sensor.setTemperatureOffset(4.0)  # uncomment to shift temperature readings by 4°C

print("AD8495 Thermocouple Reader (ESP32)")
print("Sampling every 2 seconds...")

# Infinite loop
while True:
    # Get temperature readings in celsius and fahrenheit as well as the raw voltage reading
    tempC = sensor.getTemperatureC(samples=10)
    tempF = sensor.getTemperatureF(samples=10)
    voltage = sensor.readVoltage(samples=10)

    # Print out all the values
    print("Voltage: {:.4f} V".format(voltage))
    print("Temperature: {:.2f} °C / {:.2f} °F".format(tempC, tempF))
    print("-" * 30)

    sleep(2)
