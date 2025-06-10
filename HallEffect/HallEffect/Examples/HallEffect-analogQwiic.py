# FILE: HallEffect-analogQwiic.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF:  An example of getting the magnetic field value from the Hall Effect sensor
# WORKS WITH: Hall effect sensor breakout with analog output & easyC: www.solde.red/333082
# LAST UPDATED: 2025-06-10

from HallEffect import HallEffectAnalog
from time import sleep

# If you aren't using the Qwiic connector, manually enter your I2C pins
# i2c = I2C(0, scl=Pin(22), sda=Pin(21))
# sensor = HallEffectAnalog(i2c)

# Initialize sensor over Qwiic
sensor = HallEffectAnalog()

# You can also set a custom I2C address in the initialization:
# sensor=HallEffectAnalog(address=0x31)


while 1:
    # Get raw voltage value
    analog = sensor.getReading()

    # Get the raw voltage value converted into milli Teslas
    reading = sensor.getMilliTeslas()

    # Print out the readings
    print("ADC reading:", analog)
    print("Magnetic field= ", reading, "mT")

    # Empty row
    print()
    # Pause for 1 second
    sleep(1.0)
