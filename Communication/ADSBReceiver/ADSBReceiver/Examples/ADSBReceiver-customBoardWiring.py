# FILE: ADSBReceiver-customBoardWiring.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Shows how to use this library on a custom board, where the module
#        isn't wired to the same pins as the Soldered combo board (UART1,
#        IO17/IO18/IO21). Override only the UART/pins that differ from your
#        wiring.
# LAST UPDATED: 2026-07-22

from machine import UART
from ADSBReceiver import ADSBReceiver

# Example: module on UART2, using IO4/IO5, with no RESET pin wired at all.
uart = UART(2, baudrate=115200, rx=4, tx=5, rxbuf=4096)
adsb = ADSBReceiver(uart, reset_pin=None)


# Called once per decoded aircraft update.
def onAircraft(ac):
    print("ICAO {}".format(ac.icao))


# Register the function to call whenever a decoded aircraft report arrives.
adsb.onAircraft(onAircraft)

while True:
    adsb.poll()
