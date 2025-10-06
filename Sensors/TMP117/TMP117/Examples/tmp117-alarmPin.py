# FILE: tmp117-simplePin.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  Example showing how to detect and configure an interrupt
#         on the ALR (alarm) Pin when the LOW or HIGH temperature treshold
#         is crossed
# WORKS WITH: Temperature Sensor TMP117 Breakout: www.solde.red/333175
# LAST UPDATED: 2025-09-22
from machine import I2C, Pin
import tmp117
import time

# Initialize I2C, if you're using our board, the constructor can be left blank,
# as then it will automatically be assigned to the Qwiic connector
i2c = I2C()

# Create TMP117 instance
sensor = tmp117.TMP117(i2c, addr=0x49)

# Initialize with default settings
sensor.init()


# Set alert callback
def alert_callback(pin):
    alert_type = sensor.getAlertType()
    if alert_type == tmp117.TMP117_ALERT.HIGHALERT:
        print("High temperature alert!")
    elif alert_type == tmp117.TMP117_ALERT.LOWALERT:
        print("Low temperature alert!")


# Set at what pin the ALR pin of the Breakout is connected to, as well
# as the function that will be called when an interrupt happens on that pin
sensor.setAlertCallback(alert_callback, pin=43)

# Set the lower and upper temperature tresholds for the interrupt
sensor.setAlertTemperature(20.0, 30.0)  # Set alert boundaries

# Infinite loop
while True:
    # Update sensor register values and check for new measurements
    sensor.update()
    # Read temperature
    temperature = sensor.getTemperature()
    print(f"Temperature: {temperature:.2f}°C")
    # Delay a bit until a new measurement can be made
    time.sleep(0.2)
