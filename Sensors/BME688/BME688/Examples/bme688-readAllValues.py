# FILE: bme688-readAllValues
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: An example showing how to measure and read temperature, pressure, humidity as well as
#        gas resistance using the BME688 sensor
# WORKS WITH: Environmental and Air Sensor BME688 Breakout: www.solde.red/333203
# LAST UPDATED: 2025-07-24

from bme688 import BME688  # Import BME688 module
from time import sleep  # For delay between readings
from machine import I2C, Pin  # Hardware interfaces

# Create sensor instance with default address and I2C Wiring
sensor = BME688()

# Initialize sensor with default settings
if not sensor.begin():
    print("Failed to initialize sensor!")
else:
    # Main measurement loop
    while True:
        # Read all environmental parameters
        temperature = sensor.readTemperature()  # °C
        pressure = sensor.readPressure()  # Pascals
        humidity = sensor.readHumidity()  # %RH
        gasResistance = sensor.readGas(0)  # Ohms (using profile 0)

        # Print formatted measurements
        print("\nEnvironmental Readings:")
        print("Temperature: {:.2f}°C".format(temperature))
        print("Pressure: {:.2f}Pa".format(pressure))
        print("Humidity: {:.2f}%".format(humidity))
        print("Gas Resistance: {:.2f}Ω".format(gasResistance))

        # Wait 2 seconds before next reading
        sleep(2)
