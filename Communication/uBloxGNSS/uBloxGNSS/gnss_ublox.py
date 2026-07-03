# FILE: gnss_ublox.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython driver for Soldered u-blox GPS/GNSS breakouts
# LAST UPDATED: 2026-05-22

import time
import struct

# ---------------------------------------------------------------------------
# Port identifiers
# ---------------------------------------------------------------------------
COM_PORT_I2C = 0
COM_PORT_UART1 = 1
COM_PORT_USB = 3

# Output / input protocol bitmask flags
COM_TYPE_UBX = 0x01
COM_TYPE_NMEA = 0x02
COM_TYPE_RTCM3 = 0x20

# ---------------------------------------------------------------------------
# Dynamic platform models
# ---------------------------------------------------------------------------
DYN_MODEL_PORTABLE = 0
DYN_MODEL_STATIONARY = 2
DYN_MODEL_PEDESTRIAN = 3
DYN_MODEL_AUTOMOTIVE = 4
DYN_MODEL_SEA = 5
DYN_MODEL_AIRBORNE1g = 6
DYN_MODEL_AIRBORNE2g = 7
DYN_MODEL_AIRBORNE4g = 8
DYN_MODEL_WRIST = 9
DYN_MODEL_BIKE = 10
DYN_MODEL_UNKNOWN = 255

# ---------------------------------------------------------------------------
# Power management wakeup sources (UBX-RXM-PMREQ)
# ---------------------------------------------------------------------------
VAL_RXM_PMREQ_WAKEUPSOURCE_UARTRX = 0x00000008
VAL_RXM_PMREQ_WAKEUPSOURCE_EXTINT0 = 0x00000020
VAL_RXM_PMREQ_WAKEUPSOURCE_EXTINT1 = 0x00000040
VAL_RXM_PMREQ_WAKEUPSOURCE_SPICS = 0x00000080

# ---------------------------------------------------------------------------
# Configuration save sub-section masks (UBX-CFG-CFG)
# ---------------------------------------------------------------------------
VAL_CFG_SUBSEC_IOPORT = 0x00000001
VAL_CFG_SUBSEC_MSGCONF = 0x00000002
VAL_CFG_SUBSEC_INFMSG = 0x00000004
VAL_CFG_SUBSEC_NAVCONF = 0x00000008
VAL_CFG_SUBSEC_RXMCONF = 0x00000010

# ---------------------------------------------------------------------------
# Leap second source identifiers
# ---------------------------------------------------------------------------
LS_SRC_DEFAULT = 0
LS_SRC_GLONASS = 1
LS_SRC_GPS = 2
LS_SRC_SBAS = 3
LS_SRC_BEIDOU = 4
LS_SRC_GALILEO = 5
LS_SRC_AIDED = 6
LS_SRC_CONFIGURED = 7
LS_SRC_UNKNOWN = 255

# ---------------------------------------------------------------------------
# Unix epoch look-up tables (same values as SparkFun C++ library)
# ---------------------------------------------------------------------------
_DAYS_FROM_1970_TO_2020 = 18262

_DAYS_SINCE_2020 = (
    0,
    366,
    731,
    1096,
    1461,
    1827,
    2192,
    2557,
    2922,
    3288,
    3653,
    4018,
    4383,
    4749,
    5114,
    5479,
    5844,
    6210,
    6575,
    6940,
    7305,
    7671,
    8036,
    8401,
    8766,
    9132,
    9497,
    9862,
    10227,
    10593,
    10958,
    11323,
    11688,
    12054,
    12419,
    12784,
    13149,
    13515,
    13880,
    14245,
    14610,
    14976,
    15341,
    15706,
    16071,
    16437,
    16802,
    17167,
    17532,
    17898,
    18263,
    18628,
    18993,
    19359,
    19724,
    20089,
    20454,
    20820,
    21185,
    21550,
    21915,
    22281,
    22646,
    23011,
    23376,
    23742,
    24107,
    24472,
    24837,
    25203,
    25568,
    25933,
    26298,
    26664,
    27029,
    27394,
    27759,
    28125,
    28490,
    28855,
)

# [0] = leap year, [1] = normal year
_DAYS_SINCE_MONTH = (
    (0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335),
    (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334),
)

# ---------------------------------------------------------------------------
# UBX class / ID constants
# ---------------------------------------------------------------------------
_CLS_NAV = 0x01
_CLS_RXM = 0x02
_CLS_CFG = 0x06
_CLS_MON = 0x0A

_ID_NAV_PVT = 0x07
_ID_NAV_TIMELS = 0x26

_ID_CFG_PRT = 0x00
_ID_CFG_RST = 0x04
_ID_CFG_RATE = 0x08
_ID_CFG_CFG = 0x09
_ID_CFG_RXM = 0x11
_ID_CFG_NAV5 = 0x24

_ID_MON_VER = 0x04

_ID_RXM_PMREQ = 0x41

# ACK class
_CLS_ACK = 0x05
_ID_ACK_ACK = 0x01
_ID_ACK_NACK = 0x00


def _ubxChecksum(data):
    """Fletcher-8 checksum over class+id+len(2)+payload bytes."""
    a = 0
    b = 0
    for byte in data:
        a = (a + byte) & 0xFF
        b = (b + a) & 0xFF
    return a, b


class SolderedGNSS:
    """MicroPython driver for Soldered u-blox GPS/GNSS breakout boards.

    Communicates with u-blox modules via I2C (DDC interface, default
    address 0x42) using the UBX binary protocol.
    """

    def __init__(self):
        self._i2c = None
        self._addr = 0x42

        # Cached NAV-PVT fields
        self._pvt = {
            "iTOW": 0,
            "year": 0,
            "month": 0,
            "day": 0,
            "hour": 0,
            "min": 0,
            "sec": 0,
            "nano": 0,
            "valid": 0,
            "flags": 0,
            "flags2": 0,
            "fixType": 0,
            "numSV": 0,
            "lon": 0,
            "lat": 0,
            "height": 0,
            "hMSL": 0,
            "hAcc": 0,
            "vAcc": 0,
            "gSpeed": 0,
            "headMot": 0,
            "sAcc": 0,
            "headAcc": 0,
            "pDOP": 0,
        }

        # Cached NAV-TIMELS fields
        self._timels = {
            "srcOfCurrLs": 0,
            "currLs": 0,
            "lsChange": 0,
            "timeToLsEvent": 0,
            "valid": 0,
        }

        # Protocol version cache (filled by getProtocolVersion)
        self._protoHigh = 0
        self._protoLow = 0
        self._protoQueried = False

        # Module info cache (filled by getModuleInfo)
        self.minfo = {
            "swVersion": "",
            "hwVersion": "",
            "extensions": [],
        }

        # NMEA receive buffer
        self._nmeaBuf = ""
        self._nmeaLines = []

        # I2C stream re-assembly buffer for partial UBX frames
        self._rxBuf = bytearray()

    # -----------------------------------------------------------------------
    # Initialisation
    # -----------------------------------------------------------------------

    def begin(self, i2c, addr=0x42, timeout_ms=1100):
        """Connect to the u-blox module. Returns True if the module responds."""
        self._i2c = i2c
        self._addr = addr
        try:
            self._i2c.readfrom(self._addr, 1)
        except OSError:
            return False
        # Try to get one valid PVT packet as a liveness check
        return (
            self._pollAndWait(_CLS_NAV, _ID_NAV_PVT, timeout_ms=timeout_ms) is not None
        )

    def isConnected(self, timeout_ms=1100):
        """Return True if the module is still reachable."""
        return (
            self._pollAndWait(_CLS_NAV, _ID_NAV_PVT, timeout_ms=timeout_ms) is not None
        )

    # -----------------------------------------------------------------------
    # NAV-PVT — position/velocity/time
    # -----------------------------------------------------------------------

    def getPVT(self, timeout_ms=1100):
        """Poll the module and cache fresh PVT data. Returns True on success."""
        payload = self._pollAndWait(_CLS_NAV, _ID_NAV_PVT, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 84:
            return False
        p = payload
        self._pvt["iTOW"] = struct.unpack_from("<I", p, 0)[0]
        self._pvt["year"] = struct.unpack_from("<H", p, 4)[0]
        self._pvt["month"] = p[6]
        self._pvt["day"] = p[7]
        self._pvt["hour"] = p[8]
        self._pvt["min"] = p[9]
        self._pvt["sec"] = p[10]
        self._pvt["valid"] = p[11]
        self._pvt["nano"] = struct.unpack_from("<i", p, 16)[0]
        self._pvt["fixType"] = p[20]
        self._pvt["flags"] = p[21]
        self._pvt["flags2"] = p[22]
        self._pvt["numSV"] = p[23]
        self._pvt["lon"] = struct.unpack_from("<i", p, 24)[0]
        self._pvt["lat"] = struct.unpack_from("<i", p, 28)[0]
        self._pvt["height"] = struct.unpack_from("<i", p, 32)[0]
        self._pvt["hMSL"] = struct.unpack_from("<i", p, 36)[0]
        self._pvt["hAcc"] = struct.unpack_from("<I", p, 40)[0]
        self._pvt["vAcc"] = struct.unpack_from("<I", p, 44)[0]
        self._pvt["gSpeed"] = struct.unpack_from("<i", p, 60)[0]
        self._pvt["headMot"] = struct.unpack_from("<i", p, 64)[0]
        self._pvt["sAcc"] = struct.unpack_from("<I", p, 68)[0]
        self._pvt["headAcc"] = struct.unpack_from("<I", p, 72)[0]
        self._pvt["pDOP"] = struct.unpack_from("<H", p, 76)[0]
        return True

    def getLatitude(self):
        """Return latitude in degrees * 10^-7."""
        return self._pvt["lat"]

    def getLongitude(self):
        """Return longitude in degrees * 10^-7."""
        return self._pvt["lon"]

    def getAltitude(self):
        """Return height above WGS-84 ellipsoid in mm."""
        return self._pvt["height"]

    def getAltitudeMSL(self):
        """Return height above Mean Sea Level in mm."""
        return self._pvt["hMSL"]

    def getFixType(self):
        """Return fix type: 0=no fix, 2=2D, 3=3D, 4=GNSS+DR, 5=time only."""
        return self._pvt["fixType"]

    def getSIV(self):
        """Return number of satellites used in the navigation solution."""
        return self._pvt["numSV"]

    def getYear(self):
        return self._pvt["year"]

    def getMonth(self):
        return self._pvt["month"]

    def getDay(self):
        return self._pvt["day"]

    def getHour(self):
        return self._pvt["hour"]

    def getMinute(self):
        return self._pvt["min"]

    def getSecond(self):
        return self._pvt["sec"]

    def getNanosecond(self):
        """Return nanosecond fraction of the second (range -1e9 .. 1e9)."""
        return self._pvt["nano"]

    def getTimeValid(self):
        """Return True if the UTC time of day is valid."""
        return bool(self._pvt["valid"] & 0x02)

    def getDateValid(self):
        """Return True if the UTC date is valid."""
        return bool(self._pvt["valid"] & 0x01)

    def getTimeFullyResolved(self):
        """Return True if UTC time is fully resolved (no seconds uncertainty)."""
        return bool(self._pvt["valid"] & 0x04)

    def getConfirmedTime(self):
        """Return True if UTC time validity has been confirmed."""
        return bool(self._pvt["flags2"] & 0x80)

    def getGroundSpeed(self):
        """Return 2D ground speed in mm/s."""
        return self._pvt["gSpeed"]

    def getHeading(self):
        """Return heading of motion in degrees * 10^-5."""
        return self._pvt["headMot"]

    def getSpeedAccuracy(self):
        """Return speed accuracy estimate in mm/s."""
        return self._pvt["sAcc"]

    def getHeadingAccuracy(self):
        """Return heading accuracy estimate in degrees * 10^-5."""
        return self._pvt["headAcc"]

    def getHorizontalAccuracy(self):
        """Return horizontal position accuracy estimate in mm."""
        return self._pvt["hAcc"]

    def getVerticalAccuracy(self):
        """Return vertical position accuracy estimate in mm."""
        return self._pvt["vAcc"]

    def getPDOP(self):
        """Return position DOP * 100 (divide by 100 for actual pDOP)."""
        return self._pvt["pDOP"]

    def getCarrierSolutionType(self):
        """Return RTK carrier solution: 0=none, 1=float, 2=fixed."""
        return (self._pvt["flags"] >> 6) & 0x03

    def getUnixEpoch(self):
        """Compute Unix epoch from cached PVT data.

        Returns (epoch_seconds, microseconds).
        """
        year = self._pvt["year"]
        month = self._pvt["month"]
        day = self._pvt["day"]
        hour = self._pvt["hour"]
        minute = self._pvt["min"]
        sec = self._pvt["sec"]
        nano = self._pvt["nano"]

        epoch = _DAYS_FROM_1970_TO_2020
        y = year - 2020
        if 0 <= y < len(_DAYS_SINCE_2020):
            epoch += _DAYS_SINCE_2020[y]

        leap = year % 4 == 0
        m = max(0, min(month - 1, 11))
        epoch += _DAYS_SINCE_MONTH[0 if leap else 1][m]
        epoch += day - 1
        epoch *= 86400
        epoch += hour * 3600 + minute * 60 + sec

        if nano < 0:
            epoch -= 1
            nanos = 1000000000 + nano
        else:
            nanos = nano
        micros = nanos // 1000
        return epoch, micros

    # -----------------------------------------------------------------------
    # NAV-TIMELS — leap second event information
    # -----------------------------------------------------------------------

    def getLeapSecondEvent(self, timeout_ms=1100):
        """Poll and cache leap second event info. Returns True on success."""
        payload = self._pollAndWait(_CLS_NAV, _ID_NAV_TIMELS, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 24:
            return False
        self._timels["srcOfCurrLs"] = payload[8]
        self._timels["currLs"] = struct.unpack_from("<b", payload, 9)[0]
        self._timels["lsChange"] = struct.unpack_from("<b", payload, 11)[0]
        self._timels["timeToLsEvent"] = struct.unpack_from("<i", payload, 12)[0]
        self._timels["valid"] = payload[23]
        return True

    def getLeapIndicator(self):
        """Return (li, timeToLsEvent) where li: 0=no warning, 1=+1s, 2=-1s, 3=alarm."""
        if not (self._timels["valid"] & 0x02):
            return 3, 0  # alarm — time to event unknown
        t = self._timels["timeToLsEvent"]
        c = self._timels["lsChange"]
        if c == 0:
            return 0, t
        elif c > 0:
            return 1, t
        else:
            return 2, t

    def getCurrentLeapSeconds(self):
        """Return (currLs, source) from cached NAV-TIMELS data."""
        return self._timels["currLs"], self._timels["srcOfCurrLs"]

    # -----------------------------------------------------------------------
    # MON-VER — module / protocol version
    # -----------------------------------------------------------------------

    def getProtocolVersion(self, timeout_ms=1100):
        """Poll MON-VER and extract the protocol version. Returns True on success."""
        payload = self._pollAndWait(_CLS_MON, _ID_MON_VER, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 40:
            return False
        # Extension strings start at offset 40, each 30 bytes
        ext_count = (len(payload) - 40) // 30
        for i in range(ext_count):
            start = 40 + i * 30
            ext = (
                payload[start : start + 30].split(b"\x00")[0].decode("ascii", "ignore")
            )
            if ext.startswith("PROTVER="):
                parts = ext[8:].split(".")
                try:
                    self._protoHigh = int(parts[0])
                    self._protoLow = int(parts[1]) if len(parts) > 1 else 0
                except (ValueError, IndexError):
                    pass
                break
        self._protoQueried = True
        return True

    def getProtocolVersionHigh(self, timeout_ms=1100):
        """Return major protocol version number (e.g. 27 for v27.30)."""
        if not self._protoQueried:
            self.getProtocolVersion(timeout_ms)
        return self._protoHigh

    def getProtocolVersionLow(self, timeout_ms=1100):
        """Return minor protocol version number (e.g. 30 for v27.30)."""
        if not self._protoQueried:
            self.getProtocolVersion(timeout_ms)
        return self._protoLow

    def getModuleInfo(self, timeout_ms=1100):
        """Poll MON-VER and populate the minfo dict. Returns True on success."""
        payload = self._pollAndWait(_CLS_MON, _ID_MON_VER, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 40:
            return False
        self.minfo["swVersion"] = (
            payload[0:30].split(b"\x00")[0].decode("ascii", "ignore")
        )
        self.minfo["hwVersion"] = (
            payload[30:40].split(b"\x00")[0].decode("ascii", "ignore")
        )
        ext_count = (len(payload) - 40) // 30
        exts = []
        for i in range(ext_count):
            start = 40 + i * 30
            ext = (
                payload[start : start + 30].split(b"\x00")[0].decode("ascii", "ignore")
            )
            exts.append(ext)
            if ext.startswith("PROTVER="):
                parts = ext[8:].split(".")
                try:
                    self._protoHigh = int(parts[0])
                    self._protoLow = int(parts[1]) if len(parts) > 1 else 0
                except (ValueError, IndexError):
                    pass
        self.minfo["extensions"] = exts
        self._protoQueried = True
        return True

    # -----------------------------------------------------------------------
    # CFG-RATE — measurement and navigation rate
    # -----------------------------------------------------------------------

    def getMeasurementRate(self, timeout_ms=1100):
        """Return current measurement interval in ms."""
        payload = self._pollAndWait(_CLS_CFG, _ID_CFG_RATE, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 6:
            return 0
        return struct.unpack_from("<H", payload, 0)[0]

    def getNavigationRate(self, timeout_ms=1100):
        """Return current navigation rate (measurements per solution)."""
        payload = self._pollAndWait(_CLS_CFG, _ID_CFG_RATE, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 6:
            return 0
        return struct.unpack_from("<H", payload, 2)[0]

    def setMeasurementRate(self, rate_ms, timeout_ms=1100):
        """Set measurement interval in ms. Returns True if ACKed."""
        payload = self._pollAndWait(_CLS_CFG, _ID_CFG_RATE, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 6:
            return False
        p = bytearray(payload)
        struct.pack_into("<H", p, 0, rate_ms)
        return self._sendAndAck(_CLS_CFG, _ID_CFG_RATE, bytes(p), timeout_ms)

    def setNavigationRate(self, nav_rate, timeout_ms=1100):
        """Set navigation ratio (measurements per solution). Returns True if ACKed."""
        payload = self._pollAndWait(_CLS_CFG, _ID_CFG_RATE, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 6:
            return False
        p = bytearray(payload)
        struct.pack_into("<H", p, 2, nav_rate)
        return self._sendAndAck(_CLS_CFG, _ID_CFG_RATE, bytes(p), timeout_ms)

    def setNavigationFrequency(self, hz, timeout_ms=1100):
        """Set navigation frequency in Hz (1-10). Returns True if ACKed."""
        if hz <= 0:
            return False
        return self.setMeasurementRate(1000 // hz, timeout_ms)

    def getNavigationFrequency(self, timeout_ms=1100):
        """Return current navigation frequency in Hz."""
        rate = self.getMeasurementRate(timeout_ms)
        if rate == 0:
            return 0
        return 1000 // rate

    # -----------------------------------------------------------------------
    # CFG-NAV5 — navigation engine settings (dynamic model)
    # -----------------------------------------------------------------------

    def setDynamicModel(self, model=DYN_MODEL_PORTABLE, timeout_ms=1100):
        """Set the dynamic platform model. Returns True if ACKed."""
        payload = self._pollAndWait(_CLS_CFG, _ID_CFG_NAV5, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 36:
            return False
        p = bytearray(payload)
        # mask: bit0 = dyn model, bit1 = fixMode, etc.
        struct.pack_into("<H", p, 0, 0x0001)  # apply dynModel only
        p[2] = model
        return self._sendAndAck(_CLS_CFG, _ID_CFG_NAV5, bytes(p), timeout_ms)

    def getDynamicModel(self, timeout_ms=1100):
        """Return the current dynamic platform model (255 on failure)."""
        payload = self._pollAndWait(_CLS_CFG, _ID_CFG_NAV5, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 36:
            return DYN_MODEL_UNKNOWN
        return payload[2]

    # -----------------------------------------------------------------------
    # CFG-PRT — port configuration (I2C output type and address)
    # -----------------------------------------------------------------------

    def _getCfgPrt(self, timeout_ms=1100):
        """Poll CFG-PRT for the I2C (DDC) port. Returns raw 20-byte payload."""
        return self._pollAndWait(
            _CLS_CFG,
            _ID_CFG_PRT,
            poll_payload=bytes([COM_PORT_I2C]),
            timeout_ms=timeout_ms,
        )

    def setI2COutput(self, com_type, timeout_ms=1100):
        """Configure I2C output protocol mask. Returns True if ACKed."""
        payload = self._getCfgPrt(timeout_ms)
        if payload is None or len(payload) < 20:
            return False
        p = bytearray(payload)
        struct.pack_into("<H", p, 14, com_type)
        return self._sendAndAck(_CLS_CFG, _ID_CFG_PRT, bytes(p), timeout_ms)

    def setI2CAddress(self, new_addr, timeout_ms=1100):
        """Change the module's I2C address. Saved to flash on next saveConfiguration().

        new_addr: 7-bit I2C address (0x08 – 0x77).
        Returns True if ACKed; the bus address will change immediately.
        """
        payload = self._getCfgPrt(timeout_ms)
        if payload is None or len(payload) < 20:
            return False
        p = bytearray(payload)
        # The mode field encodes the slave address in bits [7:1] (7-bit addr << 1)
        mode = struct.unpack_from("<I", p, 4)[0]
        mode = (mode & ~0xFE) | ((new_addr & 0x7F) << 1)
        struct.pack_into("<I", p, 4, mode)
        result = self._sendAndAck(_CLS_CFG, _ID_CFG_PRT, bytes(p), timeout_ms)
        if result:
            self._addr = new_addr
        return result

    def setI2CpollingWait(self, ms):
        """No-op in MicroPython (included for API compatibility)."""
        pass

    # -----------------------------------------------------------------------
    # CFG-CFG — save / clear / load configuration
    # -----------------------------------------------------------------------

    def saveConfiguration(self, timeout_ms=1100):
        """Save all current settings to flash and BBR. Returns True if ACKed."""
        payload = struct.pack("<IIBB", 0x00000000, 0x0000FFFF, 0x00000000, 0)
        # clearMask=0, saveMask=0xFFFF, loadMask=0 — 12 bytes
        pl = struct.pack("<III", 0, 0x0000FFFF, 0)
        return self._sendAndAck(_CLS_CFG, _ID_CFG_CFG, pl, timeout_ms)

    def saveConfigSelective(self, mask, timeout_ms=1100):
        """Save only the selected configuration sections. Returns True if ACKed."""
        pl = struct.pack("<III", 0, mask, 0)
        return self._sendAndAck(_CLS_CFG, _ID_CFG_CFG, pl, timeout_ms)

    # -----------------------------------------------------------------------
    # Reset commands (CFG-RST)
    # -----------------------------------------------------------------------

    def hardReset(self):
        """Cold start — clears all navigation data and restarts the module."""
        # navBbrMask=0xFFFF (clear all), resetMode=0x00 (hardware reset)
        self._sendUBX(_CLS_CFG, _ID_CFG_RST, struct.pack("<HBB", 0xFFFF, 0x00, 0x00))

    def softwareResetGNSSOnly(self):
        """Controlled software reset of the GNSS subsystem only."""
        # navBbrMask=0x0000 (hot start), resetMode=0x01 (GNSS only)
        self._sendUBX(_CLS_CFG, _ID_CFG_RST, struct.pack("<HBB", 0x0000, 0x01, 0x00))

    def factoryReset(self):
        """Erase all settings from flash/BBR and perform a cold start."""
        pl = bytearray(13)
        struct.pack_into("<I", pl, 0, 0x0000FFFF)  # clearMask
        struct.pack_into("<I", pl, 8, 0x0000FFFF)  # loadMask (restore defaults)
        pl[12] = 0xFF  # deviceMask: all
        self._sendUBX(_CLS_CFG, _ID_CFG_CFG, bytes(pl))
        time.sleep_ms(100)
        self.hardReset()

    # -----------------------------------------------------------------------
    # CFG-RXM — power save mode (M8 modules only, not ZED-F9P)
    # -----------------------------------------------------------------------

    def powerSaveMode(self, enable=True, timeout_ms=1100):
        """Enable or disable UBX-CFG-RXM power save mode. Returns True if ACKed."""
        payload = self._pollAndWait(_CLS_CFG, _ID_CFG_RXM, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 2:
            return False
        p = bytearray(payload)
        p[1] = 1 if enable else 0  # lpMode
        return self._sendAndAck(_CLS_CFG, _ID_CFG_RXM, bytes(p), timeout_ms)

    def getPowerSaveMode(self, timeout_ms=1100):
        """Return lpMode value: 0=continuous, 1=power save (255 on failure)."""
        payload = self._pollAndWait(_CLS_CFG, _ID_CFG_RXM, timeout_ms=timeout_ms)
        if payload is None or len(payload) < 2:
            return 255
        return payload[1]

    # -----------------------------------------------------------------------
    # RXM-PMREQ — power off / wake
    # -----------------------------------------------------------------------

    def powerOff(self, duration_ms):
        """Put the module into backup (power-off) mode for duration_ms ms.

        The module wakes automatically after duration_ms (0 = indefinite).
        While powered off, avoid sending I2C traffic to the module.
        """
        # Version 0 packet (8 bytes): duration + flags(backup=1)
        self._sendUBX(_CLS_RXM, _ID_RXM_PMREQ, struct.pack("<II", duration_ms, 0x02))

    def powerOffWithInterrupt(
        self,
        duration_ms,
        wakeup_sources=VAL_RXM_PMREQ_WAKEUPSOURCE_EXTINT0,
        force_while_usb=True,
    ):
        """Put the module into backup mode; specify hardware wakeup sources.

        wakeup_sources: OR of VAL_RXM_PMREQ_WAKEUPSOURCE_* constants.
        """
        # Version 1 packet (16 bytes)
        pl = bytearray(16)
        pl[0] = 1  # version
        struct.pack_into("<I", pl, 4, duration_ms)
        struct.pack_into("<I", pl, 8, 0x02)  # flags: backup
        struct.pack_into("<I", pl, 12, wakeup_sources)
        self._sendUBX(_CLS_RXM, _ID_RXM_PMREQ, bytes(pl))

    # -----------------------------------------------------------------------
    # NMEA pass-through
    # -----------------------------------------------------------------------

    def checkUblox(self):
        """Read all pending bytes from the I2C stream, accumulate NMEA lines."""
        avail = self._bytesAvailable()
        while avail > 0:
            chunk = min(avail, 64)
            try:
                data = self._readFromStream(chunk)
            except OSError:
                break
            for b in data:
                c = chr(b)
                if c == "$":
                    self._nmeaBuf = "$"
                elif self._nmeaBuf:
                    if c == "\n":
                        self._nmeaLines.append(self._nmeaBuf.rstrip("\r"))
                        self._nmeaBuf = ""
                    else:
                        self._nmeaBuf += c
            avail -= chunk

    def readNMEA(self):
        """Return all buffered NMEA sentences and clear the buffer."""
        lines = self._nmeaLines
        self._nmeaLines = []
        return lines

    # -----------------------------------------------------------------------
    # Internal UBX protocol implementation
    # -----------------------------------------------------------------------

    def _sendUBX(self, cls, id_, payload=b""):
        """Assemble and send a UBX frame over I2C."""
        plen = len(payload)
        frame = bytearray([0xB5, 0x62, cls, id_, plen & 0xFF, (plen >> 8) & 0xFF])
        frame += payload
        ck_a, ck_b = _ubxChecksum(frame[2:])
        frame += bytes([ck_a, ck_b])
        self._i2c.writeto(self._addr, frame)

    def _bytesAvailable(self):
        """Return number of bytes waiting in the module's I2C output buffer."""
        try:
            data = self._i2c.readfrom_mem(self._addr, 0xFD, 2)
            n = (data[0] << 8) | data[1]
            return 0 if n == 0xFFFF else n
        except OSError:
            return 0

    def _readFromStream(self, n):
        """Read n bytes from register 0xFF (the data stream)."""
        result = bytearray()
        remaining = n
        while remaining > 0:
            chunk = min(remaining, 32)
            # Write register address 0xFF with repeated start, then read
            self._i2c.writeto(self._addr, bytes([0xFF]), False)
            result += self._i2c.readfrom(self._addr, chunk)
            remaining -= chunk
        return bytes(result)

    def _parseUBXFromBuf(self, buf, cls, id_):
        """Scan buf for a matching UBX frame. Returns (payload, consumed_end) or (None, 0)."""
        i = 0
        while i < len(buf) - 5:
            if buf[i] == 0xB5 and buf[i + 1] == 0x62:
                if i + 6 > len(buf):
                    break
                msg_cls = buf[i + 2]
                msg_id = buf[i + 3]
                msg_len = buf[i + 4] | (buf[i + 5] << 8)
                total = i + 6 + msg_len + 2
                if total > len(buf):
                    break  # frame incomplete — wait for more bytes

                payload = buf[i + 6 : i + 6 + msg_len]
                ck_a = buf[total - 2]
                ck_b = buf[total - 1]
                exp_a, exp_b = _ubxChecksum(buf[i + 2 : i + 6 + msg_len])
                if ck_a == exp_a and ck_b == exp_b:
                    if msg_cls == cls and msg_id == id_:
                        return bytes(payload), total
                i += 1
            else:
                i += 1
        return None, 0

    def _waitForUBX(self, cls, id_, timeout_ms):
        """Wait up to timeout_ms for a UBX frame matching cls/id_. Returns payload or None."""
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        buf = bytearray(self._rxBuf)

        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            avail = self._bytesAvailable()
            if avail > 0:
                chunk = min(avail, 64)
                try:
                    buf += self._readFromStream(chunk)
                except OSError:
                    time.sleep_ms(5)
                    continue

            payload, end = self._parseUBXFromBuf(buf, cls, id_)
            if payload is not None:
                self._rxBuf = bytearray(buf[end:])
                return payload

            # Trim oversized buffer (keep most-recent 512 bytes)
            if len(buf) > 512:
                buf = buf[-512:]

            time.sleep_ms(5)

        self._rxBuf = bytearray()
        return None

    def _pollAndWait(self, cls, id_, poll_payload=b"", timeout_ms=1100):
        """Send a UBX poll request and wait for the matching response."""
        try:
            self._sendUBX(cls, id_, poll_payload)
        except OSError:
            return None
        return self._waitForUBX(cls, id_, timeout_ms)

    def _waitForAck(self, cls, id_, timeout_ms):
        """Wait for ACK-ACK or ACK-NACK for a given cls/id. Returns True on ACK."""
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        buf = bytearray(self._rxBuf)

        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            avail = self._bytesAvailable()
            if avail > 0:
                chunk = min(avail, 64)
                try:
                    buf += self._readFromStream(chunk)
                except OSError:
                    time.sleep_ms(5)
                    continue

            # Scan for ACK
            i = 0
            while i < len(buf) - 5:
                if buf[i] == 0xB5 and buf[i + 1] == 0x62:
                    if i + 6 > len(buf):
                        break
                    msg_cls = buf[i + 2]
                    msg_id = buf[i + 3]
                    msg_len = buf[i + 4] | (buf[i + 5] << 8)
                    total = i + 6 + msg_len + 2
                    if total > len(buf):
                        break
                    if msg_cls == _CLS_ACK and msg_len == 2:
                        ack_cls = buf[i + 6]
                        ack_id = buf[i + 7]
                        if ack_cls == cls and ack_id == id_:
                            self._rxBuf = bytearray(buf[total:])
                            return msg_id == _ID_ACK_ACK
                    i += 1
                else:
                    i += 1

            if len(buf) > 512:
                buf = buf[-512:]

            time.sleep_ms(5)

        self._rxBuf = bytearray()
        return False

    def _sendAndAck(self, cls, id_, payload, timeout_ms=1100):
        """Send a UBX command and wait for ACK. Returns True on ACK-ACK."""
        try:
            self._sendUBX(cls, id_, payload)
        except OSError:
            return False
        return self._waitForAck(cls, id_, timeout_ms)
