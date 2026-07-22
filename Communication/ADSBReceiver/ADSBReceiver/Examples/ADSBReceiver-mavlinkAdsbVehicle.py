# FILE: ADSBReceiver-mavlinkAdsbVehicle.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Switches the module to MAVLink output and decodes the ADSB_VEHICLE
#        message it sends for every tracked aircraft. Also shows the generic
#        frame callback, which fires for any MAVLink message the module sends.
# LAST UPDATED: 2026-07-22

from machine import UART
from ADSBReceiver import ADSBReceiver, DECODED_PROTOCOL_MAVLINK

uart = UART(1, baudrate=115200, rx=17, tx=18, rxbuf=4096)
adsb = ADSBReceiver(uart, reset_pin=21)


# Called once per decoded ADSB_VEHICLE message, one per tracked aircraft.
def onAdsbVehicle(v):
    line = "ICAO {:X}".format(v.icaoAddress)
    if v.hasValidCallsign():
        line += "  call={}".format(v.callsign)
    if v.hasValidCoords():
        line += "  lat={:.5f} lon={:.5f}".format(v.latDegrees(), v.lonDegrees())
    if v.hasValidAltitude():
        line += "  alt={}m".format(v.altitudeMeters())
    if v.hasValidVelocity():
        line += "  vel={}m/s".format(v.horVelocity / 100.0)
    if v.hasValidSquawk():
        line += "  squawk={}".format(v.squawk)
    line += "  tslc={}s".format(v.tslc)
    print(line)


# Called for every MAVLink frame received, whatever its message id.
def onFrame(f):
    payload_hex = "".join("{:02X}".format(b) for b in f.payload)
    print(
        "[mavlink] msgid={} sysid={} crcValid={} payload={}".format(
            f.msgid, f.sysid, "yes" if f.crcValid else "no", payload_hex
        )
    )


# Register the callbacks that will receive the decoded and raw MAVLink data.
adsb.onMavlinkAdsbVehicle(onAdsbVehicle)
adsb.onMavlinkFrame(onFrame)

# The module defaults to CSV output, so switch it to MAVLink here.
if adsb.enterConfiguration():
    adsb.setAdsbRxProtocolDecoded(DECODED_PROTOCOL_MAVLINK)
    adsb.exitConfiguration(115200)

while True:
    adsb.poll()
