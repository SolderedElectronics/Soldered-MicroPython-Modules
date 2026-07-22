# FILE: ADSBReceiver.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Driver for the Aerobits TT-SC1b OEM ADS-B receiver module (Basic/SC1
#        tier), wired via UART. Implements the AT-command configuration/
#        state-machine layer, the module's CSV data protocol, and its MAVLink
#        data protocol (ADSB_VEHICLE message decoding).
# LAST UPDATED: 2026-07-22

import time
from machine import Pin

from AdsbAircraft import AdsbAircraft
from AdsbStats import AdsbStats
from SystemStats import SystemStats
from MavlinkFrame import MavlinkFrame
from MavlinkAdsbVehicle import MavlinkAdsbVehicle

# AT+ADSB_RX_PROTOCOL_DECODED setting values (Basic-tier module).
DECODED_PROTOCOL_NONE = 0
DECODED_PROTOCOL_CSV = 1
DECODED_PROTOCOL_MAVLINK = 2

# AT+SYSTEM_STATISTICS / AT+ADSB_STATISTICS setting values (Basic-tier module).
STATS_PROTOCOL_NONE = 0
STATS_PROTOCOL_CSV = 1

# AT+BAUDRATE setting values, applies to the main UART in RUN state.
BAUDRATE_115200 = 0
BAUDRATE_921600 = 1
BAUDRATE_3000000 = 2
BAUDRATE_57600 = 3

# AT+ADSB_RX_PROTOCOL_INC setting values: how often aircraft reports are sent.
INC_MODE_ALWAYS_ONCE_PER_SECOND = 0
INC_MODE_ONCE_PER_SECOND_IF_UPDATED = 1
INC_MODE_IMMEDIATE_ON_POSITION_UPDATE = 2

_MAVLINK_STATE_IDLE = 0
_MAVLINK_STATE_HEADER = 1
_MAVLINK_STATE_PAYLOAD = 2
_MAVLINK_STATE_CHECKSUM = 3
_MAVLINK_STATE_SIGNATURE = 4

# MAVLink CRC_EXTRA bytes for message IDs this library can verify the checksum for.
_MAVLINK_CRC_EXTRA = {
    0: 50,  # HEARTBEAT, sent once a second alongside ADSB_VEHICLE
    246: 184,  # ADSB_VEHICLE, the aircraft data this module actually sends
}


def _readLE16(buf, offset):
    return buf[offset] | (buf[offset + 1] << 8)


def _readLE32(buf, offset):
    return buf[offset] | (buf[offset + 1] << 8) | (buf[offset + 2] << 16) | (buf[offset + 3] << 24)


def _toSigned16(v):
    return v - 0x10000 if v & 0x8000 else v


def _toSigned32(v):
    return v - 0x100000000 if v & 0x80000000 else v


class ADSBReceiver:
    """Driver for the Aerobits TT-SC1b OEM ADS-B receiver module (Basic/SC1 tier).

    This targets the base "SC1" hardware tier, which only outputs CSV or
    MAVLink - no JSON/GDL90/ASTERIX/RAW HEX/BEAST, and no Mode-A/C/S decode
    or multilateration timestamps (those need the SC1-EXT variant).
    """

    def __init__(self, uart, reset_pin=None):
        """
        :param uart: machine.UART, already constructed and open (e.g.
                     UART(1, baudrate=115200, rx=17, tx=18, rxbuf=4096)). Size its rx
                     buffer at construction - dense ADS-B traffic can overflow the
                     default and silently truncate/corrupt lines if it fills before
                     poll() drains it.
        :param reset_pin: int or None, GPIO wired to the module's RESET pin. None if
                     not connected, to disable hardwareReset().
        """
        self._uart = uart
        self._reset_pin = Pin(reset_pin, Pin.IN) if reset_pin is not None else None

        self._line_buffer = ""

        self._cb_aircraft = None
        self._cb_adsb_stats = None
        self._cb_system_stats = None
        self._cb_unknown_line = None
        self._cb_line = None
        self._cb_mavlink_frame = None
        self._cb_mavlink_adsb_vehicle = None

        self._mavlink_state = _MAVLINK_STATE_IDLE
        self._mavlink_version = 0
        self._mavlink_header_buf = bytearray(9)
        self._mavlink_header_needed = 0
        self._mavlink_header_got = 0
        self._mavlink_incompat_flags = 0
        self._mavlink_seq = 0
        self._mavlink_sysid = 0
        self._mavlink_compid = 0
        self._mavlink_msgid = 0
        self._mavlink_payload = bytearray(255)
        self._mavlink_payload_len = 0
        self._mavlink_payload_got = 0
        self._mavlink_crc_running = 0xFFFF
        self._mavlink_crc_buf = bytearray(2)
        self._mavlink_crc_got = 0
        self._mavlink_signature_got = 0

    def hardwareReset(self, pulse_ms=20, active_low=True, resync_to_baud=115200):
        """
        Hardware-resets the module by toggling the RESET pin, instead of requiring a
        manual button/jumper. After this call the module is restarting: it enters
        BOOTLOADER state at the fixed 115200bps for ~3s, then auto-transitions to RUN
        unless locked. Any bytes left over from before the reset are discarded.

        :param pulse_ms: int, how long to hold the module in reset
        :param active_low: bool, True if the module resets while RESET is driven low (typical)
        :param resync_to_baud: int or None, also switch the local UART to this baud
                     (typically 115200, matching the guaranteed post-reset BOOTLOADER baud) so
                     a subsequent enterConfiguration()/command exchange isn't sent at a stale
                     baud. None to leave the UART baud untouched.
        :returns: bool, False if no reset_pin was given to the constructor (no-op)
        """
        if self._reset_pin is None:
            return False

        self._reset_pin.init(Pin.OUT)
        self._reset_pin.value(0 if active_low else 1)
        time.sleep_ms(pulse_ms)
        self._reset_pin.init(Pin.IN)  # release back to high-Z rather than holding a guessed idle level

        while self._uart.any():
            self._uart.read()
        self._line_buffer = ""

        if resync_to_baud is not None:
            self._uart.init(baudrate=resync_to_baud)

        return True

    # ---------------------------------------------------------------
    # Low level AT-command transport
    # ---------------------------------------------------------------

    def sendAT(self, body, timeout_ms=500, wait_for_prefix=None):
        """
        Send one AT command and collect the module's reply.

        :param body: str, command body without leading "AT+" and without line ending,
                     e.g. "SERIAL_NUMBER?", "SYSTEM_LOG=1", "CONFIG=0"
        :param timeout_ms: int, time to wait for a terminal line before giving up
        :param wait_for_prefix: str or None, if given, keeps listening past any generic
                     "AT+OK" and only stops once a line starting with this exact prefix (or
                     an "AT+ERROR") is seen. Needed for commands like CONFIG=1 that get a
                     generic AT+OK write-ack *before* the real state-transition marker
                     (AT+CONFIG_START) - see enterConfiguration().
        :returns: tuple(bool, str), (True, response) if a terminal line was seen before the
                     timeout: normally AT+OK, AT+ERROR or a state-transition marker; or, if
                     wait_for_prefix is given, a line starting with it or AT+ERROR.

        Any non-AT line received while waiting (e.g. CSV traffic still in flight during a
        RUN->CONFIG transition) is forwarded to the normal data callbacks instead of being
        discarded.
        """
        # A query (e.g. "SERIAL_NUMBER?", "FIRMWARE_VERSION?", "<SETTING>?") only ever gets a
        # single "AT+NAME=value" reply, with no trailing AT+OK. AT+SETTINGS?/AT+HELP are
        # multi-line and go through _sendATMultiline() instead, so this only ever applies to
        # genuine single-line queries. Ignored when wait_for_prefix is given.
        is_query = wait_for_prefix is None and body.endswith("?")

        while self._uart.any():
            self._uart.read()
        self._line_buffer = ""

        self._uart.write("AT+" + body + "\r\n")

        response = ""
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)

        while time.ticks_diff(deadline, time.ticks_ms()) >= 0:
            data = self._uart.read()
            if not data:
                continue
            for b in data:
                c = chr(b)
                if c == "\r":
                    continue
                if c != "\n":
                    self._line_buffer += c
                    if len(self._line_buffer) > 512:
                        self._line_buffer = ""
                    continue
                if len(self._line_buffer) == 0:
                    continue

                line = self._line_buffer
                self._line_buffer = ""

                if line.startswith("AT+"):
                    # AT+ replies never reach _dispatchLine() (see the else branch below), so
                    # this is the only place they'd ever reach onLine() - fire it explicitly here.
                    if self._cb_line:
                        self._cb_line(line)
                    if len(response):
                        response += "\n"
                    response += line

                    if wait_for_prefix:
                        if line.startswith(wait_for_prefix) or line.startswith("AT+ERROR"):
                            return True, response
                        # else: e.g. a generic "AT+OK" write-ack or "AT+RUN_END"/"AT+CONFIG_END"
                        # exit notice arriving before the real marker - keep waiting for it.
                    elif self._isTerminalLine(line) or is_query:
                        return True, response
                else:
                    self._dispatchLine(line)  # fires onLine() itself for this line

        return False, response

    def _sendATMultiline(self, body, overall_timeout_ms=1500, quiet_ms=150):
        while self._uart.any():
            self._uart.read()
        self._line_buffer = ""

        self._uart.write("AT+" + body + "\r\n")

        out = ""
        any_line = False
        deadline = time.ticks_add(time.ticks_ms(), overall_timeout_ms)
        last_line_at = time.ticks_ms()

        while time.ticks_diff(deadline, time.ticks_ms()) >= 0:
            data = self._uart.read()
            if data:
                for b in data:
                    c = chr(b)
                    if c == "\r":
                        continue
                    if c != "\n":
                        self._line_buffer += c
                        if len(self._line_buffer) > 512:
                            self._line_buffer = ""
                        continue
                    if len(self._line_buffer) == 0:
                        continue

                    line = self._line_buffer
                    self._line_buffer = ""
                    last_line_at = time.ticks_ms()

                    if line.startswith("AT+"):
                        if self._cb_line:
                            self._cb_line(line)
                        if len(out):
                            out += "\n"
                        out += line
                        any_line = True
                    else:
                        self._dispatchLine(line)

            if any_line and time.ticks_diff(time.ticks_ms(), last_line_at) > quiet_ms:
                break

        return any_line, out

    @staticmethod
    def isOk(response):
        """
        :param response: str, raw AT response text
        :returns: bool, True if response contains "AT+OK"
        """
        return response.find("AT+OK") >= 0

    @staticmethod
    def isError(response):
        """
        :param response: str, raw AT response text
        :returns: tuple(bool, str), (True, description) if response contains "AT+ERROR"
                     with its optional parenthesized description, else (False, "")
        """
        idx = response.find("AT+ERROR")
        if idx < 0:
            return False, ""
        p1 = response.find("(", idx)
        p2 = response.find(")", idx)
        description = response[p1 + 1 : p2] if (p1 >= 0 and p2 > p1) else ""
        return True, description

    @staticmethod
    def _isTerminalLine(line):
        # AT+RUN_END and AT+CONFIG_END are exit notifications the module sends *before* the
        # real arrival marker (RUN_END -> CONFIG_START, CONFIG_END -> RUN_START) - they must
        # NOT stop the wait on their own, or enterConfiguration()/exitConfiguration() would
        # return before ever seeing the marker they actually check for.
        return (
            line.startswith("AT+OK")
            or line.startswith("AT+ERROR")
            or line.startswith("AT+CONFIG_START")
            or line.startswith("AT+RUN_START")
            or line.startswith("AT+BOOTLOADER_START")
        )

    @staticmethod
    def _extractAssignment(response, name):
        prefix = "AT+" + name + "="
        for line in response.split("\n"):
            if line.startswith(prefix):
                return True, line[len(prefix) :]
        return False, ""

    # ---------------------------------------------------------------
    # State machine
    # ---------------------------------------------------------------

    def enterConfiguration(self):
        """
        RUN -> CONFIGURATION. Sends AT+CONFIG=1, confirms the transition via AT+CONFIG?,
        then switches the local UART to 115200 (module's fixed CONFIGURATION baud).

        :returns: bool, True on success
        """
        # In practice the AT+RUN_END/AT+CONFIG_START notifications aren't always sent (observed:
        # only a generic AT+OK write-ack comes back, likely gated by the SYSTEM_LOG setting).
        # Don't gate success on an optional notification line - accept the OK, switch baud,
        # then independently confirm via AT+CONFIG? instead.
        ok, resp = self.sendAT("CONFIG=1", 1500)
        if not ok:
            return False
        if self.isError(resp)[0]:
            return False

        self._uart.init(baudrate=115200)
        time.sleep_ms(100)  # give the module a moment to actually finish switching state/baud

        ok, state = self.getConfigState()
        if not ok:
            return False
        return state == 1 or state == 2

    def exitConfiguration(self, run_baud=115200):
        """
        CONFIGURATION -> RUN. Sends AT+CONFIG=0, confirms the transition via AT+CONFIG?, then
        switches the local UART to run_baud (must match the module's stored BAUDRATE setting).

        :param run_baud: int, baud the module's BAUDRATE setting is currently stored as
        :returns: bool, True on success
        """
        # Same reasoning as enterConfiguration(): don't rely on the optional AT+RUN_START
        # notification, confirm the transition via AT+CONFIG? after switching baud.
        ok, resp = self.sendAT("CONFIG=0", 1500)
        if not ok:
            return False
        if self.isError(resp)[0]:
            return False

        self._uart.init(baudrate=run_baud)
        time.sleep_ms(100)

        ok, state = self.getConfigState()
        if not ok:
            return False
        return state == 0

    def getConfigState(self):
        """
        AT+CONFIG?

        :returns: tuple(bool, int), (True, state) where state is 0: RUN state,
                     1: CONFIGURATION at 115200, 2: CONFIGURATION at set baud
        """
        ok, value = self.getSetting("CONFIG")
        if not ok:
            return False, 0
        return True, int(value)

    def rebootToBootloader(self):
        """
        AT+REBOOT_BOOTLOADER (also sets lock, so the module stays in BOOTLOADER afterward).

        :returns: bool, True on success
        """
        ok, resp = self.sendAT("REBOOT_BOOTLOADER", 2000)
        return ok and (self.isOk(resp) or resp.find("AT+BOOTLOADER_START") >= 0)

    def reboot(self):
        """
        AT+REBOOT

        :returns: bool, True on success
        """
        ok, resp = self.sendAT("REBOOT", 2000)
        return ok and self.isOk(resp)

    def setLock(self, locked):
        """
        AT+LOCK=1 / AT+LOCK=0

        :param locked: bool
        :returns: bool, True on success
        """
        ok, resp = self.sendAT("LOCK=" + ("1" if locked else "0"), 500)
        return ok and self.isOk(resp)

    def getLock(self):
        """
        AT+LOCK?

        :returns: tuple(bool, bool), (True, locked) on success
        """
        ok, value = self.getSetting("LOCK")
        if not ok:
            return False, False
        return True, int(value) != 0

    def isBootloader(self):
        """
        AT+BOOT?

        :returns: tuple(bool, bool), (True, in_bootloader) on success
        """
        ok, value = self.getSetting("BOOT")
        if not ok:
            return False, False
        return True, int(value) != 0

    # ---------------------------------------------------------------
    # Generic settings/commands
    # ---------------------------------------------------------------

    def setSetting(self, name, value):
        """
        :param name: str, setting name, e.g. "BAUDRATE"
        :param value: str or int, setting value
        :returns: bool, True on success
        """
        ok, resp = self.sendAT(name + "=" + str(value), 500)
        return ok and self.isOk(resp)

    def getSetting(self, name):
        """
        :param name: str, setting name
        :returns: tuple(bool, str), (True, value) on success
        """
        ok, resp = self.sendAT(name + "?", 500)
        if not ok:
            return False, ""
        return self._extractAssignment(resp, name)

    def getSettingDescription(self, name):
        """
        :param name: str, setting name
        :returns: tuple(bool, str), (True, description) on success
        """
        return self._sendATMultiline(name + "=?", 800, 150)

    def getAllSettings(self):
        """
        AT+SETTINGS?

        :returns: tuple(bool, str), (True, listing) on success
        """
        return self._sendATMultiline("SETTINGS?", 1500, 150)

    def getFullHelp(self):
        """
        AT+HELP

        :returns: tuple(bool, str), (True, help text) on success
        """
        return self._sendATMultiline("HELP", 1500, 150)

    def resetSettingsToDefault(self):
        """
        AT+SETTINGS_DEFAULT

        :returns: bool, True on success
        """
        ok, resp = self.sendAT("SETTINGS_DEFAULT", 500)
        return ok and self.isOk(resp)

    def getSerialNumber(self):
        """
        :returns: tuple(bool, str), (True, serial number) on success
        """
        ok, resp = self.sendAT("SERIAL_NUMBER?", 500)
        if not ok:
            return False, ""
        return self._extractAssignment(resp, "SERIAL_NUMBER")

    def getFirmwareVersion(self):
        """
        :returns: tuple(bool, str), (True, firmware version) on success
        """
        ok, resp = self.sendAT("FIRMWARE_VERSION?", 500)
        if not ok:
            return False, ""
        return self._extractAssignment(resp, "FIRMWARE_VERSION")

    def getDeviceType(self):
        """
        AT+DEVICE?

        :returns: tuple(bool, str), (True, device type) on success
        """
        ok, resp = self.sendAT("DEVICE?", 500)
        if not ok:
            return False, ""
        return self._extractAssignment(resp, "DEVICE")

    def test(self):
        """
        AT+TEST, expects "AT+OK"

        :returns: bool, True on success
        """
        ok, resp = self.sendAT("TEST", 500)
        return ok and self.isOk(resp)

    # ---------------------------------------------------------------
    # Typed settings, Basic-tier subset
    # ---------------------------------------------------------------

    def setBaudrate(self, baudrate):
        """
        :param baudrate: int, one of the BAUDRATE_* constants
        :returns: bool, True on success
        """
        return self.setSetting("BAUDRATE", baudrate)

    def setSystemLog(self, enable):
        """
        :param enable: bool
        :returns: bool, True on success
        """
        return self.setSetting("SYSTEM_LOG", "1" if enable else "0")

    def setSystemStatisticsProtocol(self, protocol):
        """
        :param protocol: int, one of the STATS_PROTOCOL_* constants
        :returns: bool, True on success
        """
        return self.setSetting("SYSTEM_STATISTICS", protocol)

    def setAdsbRxProtocolDecoded(self, protocol):
        """
        :param protocol: int, one of the DECODED_PROTOCOL_* constants
        :returns: bool, True on success
        """
        # This setting is String-typed on the device (confirmed via AT+ADSB_RX_PROTOCOL_DECODED=?),
        # not an integer index - it must be sent as the protocol's name.
        name = "None"
        if protocol == DECODED_PROTOCOL_CSV:
            name = "CSV"
        elif protocol == DECODED_PROTOCOL_MAVLINK:
            name = "Mavlink"
        return self.setSetting("ADSB_RX_PROTOCOL_DECODED", name)

    def setAdsbRxProtocolInc(self, mode):
        """
        :param mode: int, one of the INC_MODE_* constants
        :returns: bool, True on success
        """
        return self.setSetting("ADSB_RX_PROTOCOL_INC", mode)

    def setAdsbStatisticsProtocol(self, protocol):
        """
        :param protocol: int, one of the STATS_PROTOCOL_* constants
        :returns: bool, True on success
        """
        # Same String-typed pattern as ADSB_RX_PROTOCOL_DECODED, unlike SYSTEM_STATISTICS
        # (confirmed Integer) - send the name, not a numeric index.
        return self.setSetting("ADSB_STATISTICS", "CSV" if protocol == STATS_PROTOCOL_CSV else "None")

    # ---------------------------------------------------------------
    # RUN-state data pump - CSV and MAVLink protocols
    # ---------------------------------------------------------------

    def _dispatchLine(self, raw_line):
        line = raw_line.strip()
        if len(line) == 0:
            return

        if self._cb_line:
            self._cb_line(line)

        if line.startswith("#AS:"):
            ok, s = self.parseAdsbStatsLine(line)
            if ok and self._cb_adsb_stats:
                self._cb_adsb_stats(s)
            return
        if line.startswith("#A:"):
            ok, ac = self.parseAircraftLine(line)
            if ok and self._cb_aircraft:
                self._cb_aircraft(ac)
            return
        if line.startswith("#S:"):
            ok, s = self.parseSystemStatsLine(line)
            if ok and self._cb_system_stats:
                self._cb_system_stats(s)
            return
        if self._cb_unknown_line:
            self._cb_unknown_line(line)

    def _dispatchMavlinkFrame(self, crc_valid):
        frame = MavlinkFrame()
        frame.version = self._mavlink_version
        frame.sysid = self._mavlink_sysid
        frame.compid = self._mavlink_compid
        frame.seq = self._mavlink_seq
        frame.msgid = self._mavlink_msgid
        frame.payload = bytes(self._mavlink_payload[: self._mavlink_payload_len])
        frame.crcValid = crc_valid

        if self._cb_mavlink_frame:
            self._cb_mavlink_frame(frame)

        if crc_valid and frame.msgid == 246 and self._cb_mavlink_adsb_vehicle:
            ok, vehicle = self.parseMavlinkAdsbVehicle(frame)
            if ok:
                self._cb_mavlink_adsb_vehicle(vehicle)

    @staticmethod
    def _mavlinkCrcAccumulate(data, crc):
        # CRC-16/MCRF4XX, as used by MAVLink for both v1 and v2 framing.
        tmp = data ^ (crc & 0xFF)
        tmp ^= (tmp << 4) & 0xFF
        return ((crc >> 8) ^ ((tmp << 8) & 0xFFFF) ^ ((tmp << 3) & 0xFFFF) ^ (tmp >> 4)) & 0xFFFF

    def _feedMavlinkByte(self, b):
        if self._mavlink_state == _MAVLINK_STATE_HEADER:
            self._mavlink_header_buf[self._mavlink_header_got] = b
            self._mavlink_header_got += 1
            self._mavlink_crc_running = self._mavlinkCrcAccumulate(b, self._mavlink_crc_running)
            if self._mavlink_header_got < self._mavlink_header_needed:
                return

            buf = self._mavlink_header_buf
            if self._mavlink_version == 1:
                self._mavlink_payload_len = buf[0]
                self._mavlink_seq = buf[1]
                self._mavlink_sysid = buf[2]
                self._mavlink_compid = buf[3]
                self._mavlink_msgid = buf[4]
                self._mavlink_incompat_flags = 0
            else:
                self._mavlink_payload_len = buf[0]
                self._mavlink_incompat_flags = buf[1]
                # buf[2] is compat_flags, not needed here.
                self._mavlink_seq = buf[3]
                self._mavlink_sysid = buf[4]
                self._mavlink_compid = buf[5]
                # msgid is 3 bytes, little-endian.
                self._mavlink_msgid = buf[6] | (buf[7] << 8) | (buf[8] << 16)

            self._mavlink_payload_got = 0
            self._mavlink_crc_got = 0
            self._mavlink_state = _MAVLINK_STATE_CHECKSUM if self._mavlink_payload_len == 0 else _MAVLINK_STATE_PAYLOAD

        elif self._mavlink_state == _MAVLINK_STATE_PAYLOAD:
            self._mavlink_payload[self._mavlink_payload_got] = b
            self._mavlink_payload_got += 1
            self._mavlink_crc_running = self._mavlinkCrcAccumulate(b, self._mavlink_crc_running)
            if self._mavlink_payload_got >= self._mavlink_payload_len:
                self._mavlink_crc_got = 0
                self._mavlink_state = _MAVLINK_STATE_CHECKSUM

        elif self._mavlink_state == _MAVLINK_STATE_CHECKSUM:
            self._mavlink_crc_buf[self._mavlink_crc_got] = b
            self._mavlink_crc_got += 1
            if self._mavlink_crc_got < 2:
                return

            received = self._mavlink_crc_buf[0] | (self._mavlink_crc_buf[1] << 8)
            extra = _MAVLINK_CRC_EXTRA.get(self._mavlink_msgid)
            computed = self._mavlink_crc_running
            if extra is not None:
                computed = self._mavlinkCrcAccumulate(extra, computed)
            valid = extra is not None and computed == received
            self._dispatchMavlinkFrame(valid)

            if self._mavlink_version == 2 and (self._mavlink_incompat_flags & 0x01):
                self._mavlink_signature_got = 0
                self._mavlink_state = _MAVLINK_STATE_SIGNATURE
            else:
                self._mavlink_state = _MAVLINK_STATE_IDLE

        elif self._mavlink_state == _MAVLINK_STATE_SIGNATURE:
            self._mavlink_signature_got += 1
            if self._mavlink_signature_got >= 13:
                self._mavlink_state = _MAVLINK_STATE_IDLE

    def poll(self):
        """
        Call every loop iteration while in RUN state. Non-blocking; reads all currently
        available bytes, parses complete CSV lines / MAVLink frames (auto-detected byte by
        byte, whichever the module is actually sending) and fires callbacks.

        :returns: None
        """
        data = self._uart.read()
        if not data:
            return

        for b in data:
            if self._mavlink_state != _MAVLINK_STATE_IDLE:
                self._feedMavlinkByte(b)
                continue
            if len(self._line_buffer) == 0 and (b == 0xFE or b == 0xFD):
                self._mavlink_version = 1 if b == 0xFE else 2
                self._mavlink_header_needed = 5 if self._mavlink_version == 1 else 9
                self._mavlink_header_got = 0
                self._mavlink_crc_running = 0xFFFF
                self._mavlink_state = _MAVLINK_STATE_HEADER
                continue
            c = chr(b)
            if c == "\r":
                continue
            if c == "\n":
                if len(self._line_buffer) > 0:
                    self._dispatchLine(self._line_buffer)
                    self._line_buffer = ""
                continue
            self._line_buffer += c
            if len(self._line_buffer) > 512:
                self._line_buffer = ""

    def onAircraft(self, cb):
        """
        :param cb: callable(AdsbAircraft) or None
        """
        self._cb_aircraft = cb

    def onAdsbStats(self, cb):
        """
        :param cb: callable(AdsbStats) or None
        """
        self._cb_adsb_stats = cb

    def onSystemStats(self, cb):
        """
        :param cb: callable(SystemStats) or None
        """
        self._cb_system_stats = cb

    def onUnknownLine(self, cb):
        """
        :param cb: callable(str) or None
        """
        self._cb_unknown_line = cb

    def onLine(self, cb):
        """
        Fires for every complete line received, before it is parsed/dispatched (including
        lines later recognized as #A:/#AS:/#S:). Handy to dump exactly what's on the wire
        while debugging a parsing problem.

        :param cb: callable(str) or None
        """
        self._cb_line = cb

    def onMavlinkFrame(self, cb):
        """
        Fires for every complete MAVLink frame received, regardless of message ID.
        frame.crcValid is only meaningful for message IDs this library knows the CRC_EXTRA
        for (currently HEARTBEAT id 0, and ADSB_VEHICLE id 246).

        :param cb: callable(MavlinkFrame) or None
        """
        self._cb_mavlink_frame = cb

    def onMavlinkAdsbVehicle(self, cb):
        """
        Fires for every MAVLink ADSB_VEHICLE frame that passes CRC verification.

        :param cb: callable(MavlinkAdsbVehicle) or None
        """
        self._cb_mavlink_adsb_vehicle = cb

    # ---------------------------------------------------------------
    # Stand-alone decoders (usable without an open link, e.g. on logged data)
    # ---------------------------------------------------------------

    @staticmethod
    def crc16(data):
        """
        :param data: bytes or bytearray
        :returns: int, CRC16 checksum
        """
        crc = 0xFFFF
        for byte in data:
            x = ((crc >> 8) ^ byte) & 0xFF
            x ^= x >> 4
            crc = ((crc << 8) ^ (x << 12) ^ (x << 5) ^ x) & 0xFFFF
        return ((crc >> 8) | (crc << 8)) & 0xFFFF

    @staticmethod
    def verifyCsvCrc(line):
        """
        Verifies the trailing CRC field of a '#'-prefixed CSV line.

        :param line: str
        :returns: tuple(bool, int, int), (True, computed, received) on success
        """
        line = line.strip()
        last_comma = line.rfind(",")
        if last_comma < 0:
            return False, 0, 0

        data_part = line[:last_comma]
        crc_part = line[last_comma + 1 :].strip()
        if len(crc_part) == 0:
            return False, 0, 0

        computed = ADSBReceiver.crc16(data_part.encode("ascii"))
        received = int(crc_part, 16)
        return True, computed, received

    @staticmethod
    def parseAircraftLine(line):
        """
        :param line: str, raw "#A:..." CSV line
        :returns: tuple(bool, AdsbAircraft)
        """
        line = line.strip()
        if not line.startswith("#A:"):
            return False, None

        fields = line[3:].split(",")
        if len(fields) < 17:
            return False, None

        out = AdsbAircraft()
        out.icao = fields[0]
        if fields[1]:
            out.flags = int(fields[1], 16)
        out.callsign = fields[2]
        out.squawk = fields[3]
        if fields[4] and fields[5]:
            out.hasPosition = True
            out.lat = float(fields[4])
            out.lon = float(fields[5])
        if fields[6]:
            out.hasAltBaro = True
            out.altBaro = int(fields[6])
        if fields[7]:
            out.hasTrack = True
            out.track = float(fields[7])
        if fields[8]:
            out.hasVelH = True
            out.velH = float(fields[8])
        if fields[9]:
            out.hasVelV = True
            out.velV = int(fields[9])
        if fields[10]:
            out.hasSigS = True
            out.sigS = int(fields[10])
        if fields[11]:
            out.hasSigQ = True
            out.sigQ = int(fields[11])
        out.fps = int(fields[12]) if fields[12] else 0
        if fields[13]:
            out.hasNicNac = True
            out.nicNac = int(fields[13], 16)
        if fields[14]:
            out.hasAltGeo = True
            out.altGeo = int(fields[14])
        if fields[15]:
            out.hasEcat = True
            out.ecat = int(fields[15])
        if fields[16]:
            out.crc = int(fields[16], 16)

        ok, computed, received = ADSBReceiver.verifyCsvCrc(line)
        if ok:
            out.crcValid = computed == received

        return True, out

    @staticmethod
    def parseAdsbStatsLine(line):
        """
        :param line: str, raw "#AS:..." CSV line
        :returns: tuple(bool, AdsbStats)
        """
        line = line.strip()
        if not line.startswith("#AS:"):
            return False, None

        fields = line[4:].split(",")
        if len(fields) < 4:
            return False, None

        out = AdsbStats()
        out.fpss = int(fields[0]) if fields[0] else 0
        out.fpsac = int(fields[1]) if fields[1] else 0
        out.calib = float(fields[2]) if fields[2] else 0.0
        out.crc = int(fields[3], 16) if fields[3] else 0

        ok, computed, received = ADSBReceiver.verifyCsvCrc(line)
        if ok:
            out.crcValid = computed == received

        return True, out

    @staticmethod
    def parseSystemStatsLine(line):
        """
        :param line: str, raw "#S:..." CSV line
        :returns: tuple(bool, SystemStats)
        """
        line = line.strip()
        if not line.startswith("#S:"):
            return False, None

        fields = line[3:].split(",")
        if len(fields) < 3:
            return False, None

        out = SystemStats()
        out.cpuLoad = float(fields[0]) if fields[0] else 0.0
        out.uptime = int(fields[1]) if fields[1] else 0
        out.crc = int(fields[2], 16) if fields[2] else 0

        ok, computed, received = ADSBReceiver.verifyCsvCrc(line)
        if ok:
            out.crcValid = computed == received

        return True, out

    @staticmethod
    def parseMavlinkAdsbVehicle(frame):
        """
        Decodes an already-received MAVLink frame's payload as ADSB_VEHICLE.

        :param frame: MavlinkFrame
        :returns: tuple(bool, MavlinkAdsbVehicle), (False, None) if frame.msgid isn't 246
        """
        if frame.msgid != 246:
            return False, None

        # MAVLink 2 allows the sender to trim trailing all-zero fields off the wire payload;
        # pad back up to the message's full 38-byte layout before extracting fields.
        buf = bytearray(38)
        n = min(len(frame.payload), 38)
        buf[:n] = frame.payload[:n]

        out = MavlinkAdsbVehicle()
        out.icaoAddress = _readLE32(buf, 0)
        out.lat = _toSigned32(_readLE32(buf, 4))
        out.lon = _toSigned32(_readLE32(buf, 8))
        out.altitude = _toSigned32(_readLE32(buf, 12))
        out.heading = _readLE16(buf, 16)
        out.horVelocity = _readLE16(buf, 18)
        out.verVelocity = _toSigned16(_readLE16(buf, 20))
        out.flags = _readLE16(buf, 22)
        out.squawk = _readLE16(buf, 24)
        out.altitudeType = buf[26]
        out.callsign = bytes(buf[27:35]).rstrip(b"\x00").decode("ascii", "ignore")
        out.emitterType = buf[36]
        out.tslc = buf[37]

        return True, out
