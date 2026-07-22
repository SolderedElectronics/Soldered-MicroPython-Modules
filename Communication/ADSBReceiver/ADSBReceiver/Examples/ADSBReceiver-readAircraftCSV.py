# FILE: ADSBReceiver-readAircraftCSV.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Basic example: read decoded ADS-B aircraft reports from the TT-SC1b
#        module in its default RUN state / CSV protocol, and print them.
# LAST UPDATED: 2026-07-22

from machine import UART
from ADSBReceiver import ADSBReceiver

# Open the UART link to the module at its factory-default RUN baud.
# Board default wiring: IO17 = module TX in, IO18 = module RX out, IO21 = RESET.
# Using a different board? See example ADSBReceiver-customBoardWiring.
uart = UART(1, baudrate=115200, rx=17, tx=18, rxbuf=4096)
adsb = ADSBReceiver(uart, reset_pin=21)


# Called once per decoded aircraft update, with whichever fields the module had data for.
def onAircraft(ac):
    line = "ICAO {}".format(ac.icao)
    if ac.callsign:
        line += "  call={}".format(ac.callsign)
    if ac.hasPosition:
        line += "  lat={:.5f} lon={:.5f}".format(ac.lat, ac.lon)
    if ac.hasAltBaro:
        line += "  altBaro={}ft".format(ac.altBaro)
    if ac.hasVelH:
        line += "  vel={}kt".format(ac.velH)
    if ac.squawk:
        line += "  squawk={}".format(ac.squawk)
    line += "  onGround={}".format("yes" if ac.onGround() else "no")
    line += "  crcValid={}".format("yes" if ac.crcValid else "no")
    print(line)


# Register the function to call whenever a decoded aircraft report arrives.
adsb.onAircraft(onAircraft)

print("Waiting for ADS-B traffic...")

while True:
    # Reads incoming bytes and fires the registered callbacks. Must run every loop.
    adsb.poll()
