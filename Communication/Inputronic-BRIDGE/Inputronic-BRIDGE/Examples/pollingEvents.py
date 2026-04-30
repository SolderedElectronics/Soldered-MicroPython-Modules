# FILE: pollingEvents.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Poll keyboard, mouse, and MIDI events from the Inputronic BRIDGE.
#        Uncomment the protocol block that matches your wiring.
# WORKS WITH: Inputronic BRIDGE: www.soldered.com
# LAST UPDATED: 2026-04-30

from machine import I2C, SPI, UART, Pin
from inputronic_bridge import InputronicBridge, PROTOCOL_I2C, PROTOCOL_UART, PROTOCOL_SPI
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

while True:
    events = bridge.pollEvents()

    if events.keyboard.valid:
        for i in range(events.keyboard.keyCount):
            print(events.keyboard.keys[i], end="")
        print()

    if events.mouse.valid:
        m = events.mouse
        print("Mouse X:{} Y:{} L:{} R:{} Scroll:{}".format(
            m.x, m.y, int(m.btnLeft), int(m.btnRight), m.scroll))

    if events.midi.valid:
        mid = events.midi
        print("MIDI {:02X} {:02X} {:02X}".format(mid.b1, mid.b2, mid.b3))
