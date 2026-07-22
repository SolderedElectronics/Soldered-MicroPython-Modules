# FILE: ADSBReceiver-stateMachineAndLock.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Walks through the module's full state machine: hardware RESET ->
#        BOOTLOADER -> RUN -> CONFIGURATION -> BOOTLOADER (locked) -> RUN,
#        using the RESET pin and the LOCK mechanism to hold the module in
#        BOOTLOADER on purpose.
# LAST UPDATED: 2026-07-22

import time
from machine import UART
from ADSBReceiver import ADSBReceiver

uart = UART(1, baudrate=115200, rx=17, tx=18, rxbuf=4096)
adsb = ADSBReceiver(uart, reset_pin=21)

print("Hardware-resetting the module (RESET pin)...")
if adsb.hardwareReset():
    # BOOTLOADER holds for ~3s at the fixed 115200bps, then the module
    # auto-transitions to RUN (unless locked). Wait it out before talking to it.
    time.sleep_ms(3200)
else:
    print("No reset_pin configured - skipping hardware reset, module keeps running.")

print("RUN -> CONFIGURATION")
if not adsb.enterConfiguration():
    print("Failed to enter CONFIGURATION state.")
else:
    # Ask the module to confirm which state it is actually in.
    ok, state = adsb.getConfigState()
    if ok:
        print("AT+CONFIG? = {}".format(state))

    print("CONFIGURATION -> BOOTLOADER (this also sets AT+LOCK=1)")
    if not adsb.rebootToBootloader():
        print("Failed to reboot to BOOTLOADER state.")
    else:
        # BOOTLOADER state always runs at the fixed 115200bps.
        time.sleep_ms(200)

        # Confirm the module really is in BOOTLOADER now.
        ok, inBootloader = adsb.isBootloader()
        if ok:
            print("AT+BOOT? = {}".format("1 (BOOTLOADER)" if inBootloader else "0 (CONFIGURATION)"))

        # The lock should be set, since rebootToBootloader() sets it automatically.
        ok, locked = adsb.getLock()
        if ok:
            print("AT+LOCK? = {}".format("1 (locked)" if locked else "0 (unlocked)"))

        print("Releasing lock: module will fall through to RUN state")
        adsb.setLock(False)

        # Module leaves BOOTLOADER and enters RUN at its configured run baud (115200 by default).
        time.sleep_ms(200)
        print("Done. Module should now be broadcasting in RUN state again.")

while True:
    adsb.poll()
