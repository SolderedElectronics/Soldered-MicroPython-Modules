# FILE: ADSBReceiver-deviceInfo.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Enters CONFIGURATION state and prints device identity/health
#        information: serial number, firmware version, device type, full
#        AT+HELP text and the current AT+SETTINGS? dump. Then returns the
#        module to RUN state.
# LAST UPDATED: 2026-07-22

from machine import UART
from ADSBReceiver import ADSBReceiver

uart = UART(1, baudrate=115200, rx=17, tx=18, rxbuf=4096)
adsb = ADSBReceiver(uart, reset_pin=21)

# Print every raw line the module sends, useful to see what is really happening.
adsb.onLine(lambda line: print("[module] " + line))

# Only in CONFIGURATION state can settings be read or written.
print("Entering CONFIGURATION state...")
if not adsb.enterConfiguration():
    print("Failed to enter CONFIGURATION state.")
else:
    # Read the module's serial number.
    ok, value = adsb.getSerialNumber()
    if ok:
        print("Serial number: {}".format(value))

    # Read the currently installed firmware version.
    ok, value = adsb.getFirmwareVersion()
    if ok:
        print("Firmware version: {}".format(value))

    # Read the device type string reported by the module.
    ok, value = adsb.getDeviceType()
    if ok:
        print("Device type: {}".format(value))

    # Simple connectivity check, the module should always answer AT+OK.
    print("Connection test (AT+TEST): {}".format("OK" if adsb.test() else "FAILED"))

    # Ask the module to list every setting and its current value.
    print()
    print("--- AT+SETTINGS? ---")
    ok, settings = adsb.getAllSettings()
    if ok:
        print(settings)

    # Ask the module for its full built-in help text.
    print()
    print("--- AT+HELP ---")
    ok, help_text = adsb.getFullHelp()
    if ok:
        print(help_text)

    # Leave CONFIGURATION and resume normal aircraft tracking.
    print()
    print("Returning to RUN state...")
    adsb.exitConfiguration(115200)  # must match the BAUDRATE setting printed above
