# FILE: rawHIDReadings.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Read raw HID reports from the Inputronic BRIDGE.
#        Enables continuous raw HID polling and prints each report's hex payload.
#        Uncomment the protocol block that matches your wiring.
# WORKS WITH: Inputronic BRIDGE: www.soldered.com
# LAST UPDATED: 2026-04-30

from machine import I2C, SPI, UART, Pin
from InputronicBridge import InputronicBridge, PROTOCOL_I2C, PROTOCOL_UART, PROTOCOL_SPI
import time

# ---- I2C ----
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
bridge = InputronicBridge(PROTOCOL_I2C, i2c=i2c, i2cAddr=0x50)

# ---- UART ----
# uart = UART(1, baudrate=115200, tx=Pin(15), rx=Pin(14))
# bridge = InputronicBridge(PROTOCOL_UART, uart=uart)

# ---- SPI ----
# spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
# cs = Pin(5, Pin.OUT, value=1)
# bridge = InputronicBridge(PROTOCOL_SPI, spi=spi, spiCs=cs)

print("BRIDGE connected.")

# Push raw HID bytes on every poll.
bridge.setHidRawPolling(True)

while True:
    events = bridge.pollEvents()

    if events.hidRaw.valid:
        print("HID RAW HEX:", events.hidRaw.hex)

    time.sleep_ms(30)
