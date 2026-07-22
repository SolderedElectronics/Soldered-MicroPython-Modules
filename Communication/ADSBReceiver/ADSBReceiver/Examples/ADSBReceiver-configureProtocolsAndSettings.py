# FILE: ADSBReceiver-configureProtocolsAndSettings.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Demonstrates changing every SYSTEM and ADS-B setting supported on the
#        Basic-protocols tier: decoded protocol selection (CSV/MAVLink),
#        aircraft report timing, statistics protocol, system log and baudrate.
# LAST UPDATED: 2026-07-22

from machine import UART
from ADSBReceiver import (
    ADSBReceiver,
    DECODED_PROTOCOL_CSV,
    INC_MODE_IMMEDIATE_ON_POSITION_UPDATE,
    STATS_PROTOCOL_CSV,
    BAUDRATE_115200,
)

uart = UART(1, baudrate=115200, rx=17, tx=18, rxbuf=4096)
adsb = ADSBReceiver(uart, reset_pin=21)


# Small helper to print whether a setting write succeeded.
def printResult(what, ok):
    print("{} -> {}".format(what, "AT+OK" if ok else "FAILED"))


# Settings can only be written while in CONFIGURATION state.
if not adsb.enterConfiguration():
    print("Failed to enter CONFIGURATION state.")
else:
    # --- ADS-B decoded output protocol ---
    printResult("ADSB_RX_PROTOCOL_DECODED=CSV", adsb.setAdsbRxProtocolDecoded(DECODED_PROTOCOL_CSV))

    # Reporting cadence for decoded aircraft: update ASAP after any position update.
    printResult(
        "ADSB_RX_PROTOCOL_INC=IMMEDIATE_ON_POSITION_UPDATE",
        adsb.setAdsbRxProtocolInc(INC_MODE_IMMEDIATE_ON_POSITION_UPDATE),
    )

    # Per-aircraft ADS-B statistics (frames/s, PPS calibration), see the statistics example.
    printResult("ADSB_STATISTICS=CSV", adsb.setAdsbStatisticsProtocol(STATS_PROTOCOL_CSV))

    # --- SYSTEM settings ---
    printResult("SYSTEM_LOG=0", adsb.setSystemLog(False))
    printResult("SYSTEM_STATISTICS=CSV", adsb.setSystemStatisticsProtocol(STATS_PROTOCOL_CSV))

    # Changing BAUDRATE takes effect on the *next* RUN state entry: exitConfiguration()
    # below must be told the new value so the local UART follows the module.
    printResult("BAUDRATE=BPS_115200", adsb.setBaudrate(BAUDRATE_115200))

    print("Returning to RUN state...")
    adsb.exitConfiguration(115200)
