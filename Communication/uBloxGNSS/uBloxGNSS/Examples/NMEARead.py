# FILE: NMEARead.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read and print raw NMEA sentences from a u-blox GNSS module
# LAST UPDATED: 2026-05-22

from machine import I2C, Pin
import time
from gnss_ublox import SolderedGNSS, COM_TYPE_NMEA

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
gnss = SolderedGNSS()

if not gnss.begin(i2c):
    print("u-blox GNSS not detected. Check wiring.")
    raise SystemExit

# Enable NMEA output on I2C port
gnss.setI2COutput(COM_TYPE_NMEA)

print("u-blox GNSS ready. Printing NMEA sentences:\n")

while True:
    gnss.checkUblox()
    sentences = gnss.readNMEA()
    for sentence in sentences:
        print(sentence)
    time.sleep_ms(50)
