# FILE: interruptEvents.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Interrupt-driven event reading from the Inputronic BRIDGE.
#        The BRIDGE firmware pulses the interrupt pin when new HID data
#        is available. The driver skips bus transactions when quiet,
#        saving CPU and bus bandwidth.
#        Uncomment the protocol block that matches your wiring.
# WORKS WITH: Inputronic BRIDGE: www.soldered.com
# LAST UPDATED: 2026-04-30

from machine import I2C, SPI, UART, Pin
from InputronicBridge import InputronicBridge, PROTOCOL_I2C, PROTOCOL_UART, PROTOCOL_SPI
import time

# Pin on this MCU connected to the BRIDGE interrupt output.
interruptPin = Pin(5, Pin.IN, Pin.PULL_UP)

# Optional flag set by the user callback and checked in the main loop.
newDataFlag = False


def onBridgeDataReady():
    global newDataFlag
    newDataFlag = True


# ---- I2C ----
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
bridge = InputronicBridge(
    PROTOCOL_I2C,
    i2c=i2c,
    i2cAddr=0x50,
    interruptPin=interruptPin,
    activeHigh=False,  # falling edge
    interruptCallback=onBridgeDataReady,
)

# ---- UART ----
# uart = UART(1, baudrate=115200, tx=Pin(12), rx=Pin(10))
# bridge = InputronicBridge(
#     PROTOCOL_UART, uart=uart,
#     interruptPin=interruptPin, activeHigh=False,
#     interruptCallback=onBridgeDataReady,
# )

# ---- SPI ----
# spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
# cs = Pin(10, Pin.OUT, value=1)
# bridge = InputronicBridge(
#     PROTOCOL_SPI, spi=spi, spiCs=cs,
#     interruptPin=interruptPin, activeHigh=False,
#     interruptCallback=onBridgeDataReady,
# )

print("BRIDGE connected — interrupt mode active.")

while True:
    # pollEvents() returns immediately with no bus traffic unless the
    # interrupt flag has been set by the BRIDGE.
    events = bridge.pollEvents()

    if events.keyboard.valid:
        print("Keyboard: ", end="")
        for i in range(events.keyboard.keyCount):
            print(events.keyboard.keys[i], end="")
        print()

    if events.mouse.valid:
        m = events.mouse
        print(
            "Mouse X:{} Y:{} L:{} R:{} M:{} Scroll:{}".format(
                m.x, m.y, int(m.btnLeft), int(m.btnRight), int(m.btnMiddle), m.scroll
            )
        )

    if events.midi.valid:
        mid = events.midi
        print("MIDI {:02X} {:02X} {:02X}".format(mid.b1, mid.b2, mid.b3))

    if newDataFlag:
        newDataFlag = False
        # events above already contain the latest data; use this flag
        # to trigger additional work on data arrival if needed.
