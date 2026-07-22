# FILE: ADSBReceiver-statistics.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Enables and reads the two CSV statistics messages: system health
#        ("#S:") and ADS-B receiver health ("#AS:"). Useful for monitoring
#        CPU load, uptime, received frame rate and PPS calibration.
# LAST UPDATED: 2026-07-22

from machine import UART
from ADSBReceiver import ADSBReceiver, STATS_PROTOCOL_CSV

uart = UART(1, baudrate=115200, rx=17, tx=18, rxbuf=4096)
adsb = ADSBReceiver(uart, reset_pin=21)


# Called once per second with the module's own CPU load and uptime.
def onSystemStats(s):
    print(
        "[SYSTEM] CPU load={}%  uptime={}s  crcValid={}".format(
            s.cpuLoad, s.uptime, "yes" if s.crcValid else "no"
        )
    )


# Called once per second with the ADS-B receiver frame counts and PPS calibration.
def onAdsbStats(s):
    print(
        "[ADS-B]  Mode-S fps={}  Mode-A/C fps={}  PPS calib={}  crcValid={}".format(
            s.fpss, s.fpsac, s.calib, "yes" if s.crcValid else "no"
        )
    )


# Register the callbacks that will receive the stats messages.
adsb.onSystemStats(onSystemStats)
adsb.onAdsbStats(onAdsbStats)

# Both statistics protocols default to disabled, so turn them on here.
if adsb.enterConfiguration():
    adsb.setSystemStatisticsProtocol(STATS_PROTOCOL_CSV)
    adsb.setAdsbStatisticsProtocol(STATS_PROTOCOL_CSV)
    adsb.exitConfiguration(115200)
else:
    print("Failed to enter CONFIGURATION state.")

while True:
    adsb.poll()
