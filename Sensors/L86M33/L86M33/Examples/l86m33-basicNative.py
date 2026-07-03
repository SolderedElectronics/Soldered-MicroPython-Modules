# FILE: l86m33-basicNative.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: Basic native UART example for the L86-M33 GNSS breakout - prints location, date and time
# LAST UPDATED: 2026-07-02

from l86m33 import GNSS
import time

# Adjust to your board's wiring and a free hardware UART peripheral
UART_ID = 1
TX_PIN = 23
RX_PIN = 19

gps = GNSS(UART_ID, TX_PIN, RX_PIN)

last_display = time.ticks_ms()
start_time = time.ticks_ms()

while True:
    while gps.uart.any():
        b = gps.uart.read(1)
        if b and gps.encode(b[0]):
            if time.ticks_diff(time.ticks_ms(), last_display) > 500:
                last_display = time.ticks_ms()

                print("Location: ", end="")
                if gps.location.isValid():
                    print(
                        "{:.6f},{:.6f}".format(gps.location.lat(), gps.location.lng()),
                        end="",
                    )
                else:
                    print("INVALID", end="")

                print("  Date/Time: ", end="")
                if gps.date.isValid():
                    print(
                        "{}/{}/{}".format(
                            gps.date.month(), gps.date.day(), gps.date.year()
                        ),
                        end="",
                    )
                else:
                    print("INVALID", end="")

                print(" ", end="")
                if gps.time.isValid():
                    print(
                        "{:02d}:{:02d}:{:02d}.{:02d}".format(
                            gps.time.hour(),
                            gps.time.minute(),
                            gps.time.second(),
                            gps.time.centisecond(),
                        )
                    )
                else:
                    print("INVALID")

    # No data in the first 5 seconds from startup? Something is wrong, check wiring!
    if (
        time.ticks_diff(time.ticks_ms(), start_time) > 5000
        and gps.charsProcessed() < 10
    ):
        print("No GPS detected: check wiring.")
