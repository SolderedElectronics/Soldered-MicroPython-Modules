# FILE: l86m33.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython driver for the L86-M33 GNSS breakout (native UART mode, own NMEA parser)
# LAST UPDATED: 2026-07-02

from machine import UART, Pin
import time
import math

# Maximum length of a single NMEA field (matches TinyGPS++ _GPS_MAX_FIELD_SIZE)
_MAX_FIELD_SIZE = 15

# Internal sentence type identifiers
_SENTENCE_OTHER = 0
_SENTENCE_GPGGA = 1
_SENTENCE_GPRMC = 2

# Unit conversion constants (from TinyGPS++)
_MPH_PER_KNOT = 1.15077945
_MPS_PER_KNOT = 0.51444444
_KMPH_PER_KNOT = 1.852
_MILES_PER_METER = 0.00062137112
_KM_PER_METER = 0.001
_FEET_PER_METER = 3.2808399


def _atol(term):
    """Parse a leading signed integer out of an NMEA field, 0 if none found."""
    if not term:
        return 0
    i = 0
    negative = term[0] == '-'
    if negative:
        i = 1
    j = i
    while j < len(term) and term[j].isdigit():
        j += 1
    if j == i:
        return 0
    val = int(term[i:j])
    return -val if negative else val


def _parse_decimal(term):
    """Parse a (potentially negative) number with up to 2 decimal digits (-xxxx.yy) into value*100."""
    if not term:
        return 0
    negative = term[0] == '-'
    start = 1 if negative else 0
    i = start
    while i < len(term) and term[i].isdigit():
        i += 1
    ret = 100 * (int(term[start:i]) if i > start else 0)
    if i < len(term) and term[i] == '.':
        frac = term[i + 1:]
        if len(frac) >= 1 and frac[0].isdigit():
            ret += 10 * (ord(frac[0]) - ord('0'))
            if len(frac) >= 2 and frac[1].isdigit():
                ret += ord(frac[1]) - ord('0')
    return -ret if negative else ret


def _parse_degrees(term, deg):
    """Parse NMEA DDMM.MMMM coordinate field into a RawDegrees object, in place."""
    if not term:
        deg.deg = 0
        deg.billionths = 0
        deg.negative = False
        return
    i = 0
    while i < len(term) and term[i].isdigit():
        i += 1
    left_of_decimal = int(term[:i]) if i > 0 else 0
    minutes = left_of_decimal % 100
    multiplier = 10000000
    ten_millionths_of_minutes = minutes * multiplier
    deg.deg = left_of_decimal // 100
    if i < len(term) and term[i] == '.':
        j = i + 1
        while j < len(term) and term[j].isdigit():
            multiplier //= 10
            ten_millionths_of_minutes += (ord(term[j]) - ord('0')) * multiplier
            j += 1
    deg.billionths = (5 * ten_millionths_of_minutes + 1) // 3
    deg.negative = False


class RawDegrees:
    """Raw NMEA coordinate value: whole degrees + billionths of a degree fraction."""

    def __init__(self):
        self.deg = 0
        self.billionths = 0
        self.negative = False


class _NMEAField:
    """Common valid/updated/age tracking shared by every decoded NMEA value."""

    def __init__(self):
        self.valid = False
        self.updated = False
        self._last_commit_time = 0

    def isValid(self):
        """:returns: bool, True once this field has been successfully decoded at least once"""
        return self.valid

    def isUpdated(self):
        """:returns: bool, True if this field changed since it was last read"""
        return self.updated

    def age(self):
        """:returns: int, milliseconds since this field was last decoded, or 0xFFFFFFFF if never valid"""
        if self.valid:
            return time.ticks_diff(time.ticks_ms(), self._last_commit_time)
        return 0xFFFFFFFF


class NMEALocation(_NMEAField):
    """Decoded latitude/longitude from GPRMC/GPGGA sentences."""

    def __init__(self):
        super().__init__()
        self.raw_lat = RawDegrees()
        self.raw_lng = RawDegrees()
        self.raw_new_lat = RawDegrees()
        self.raw_new_lng = RawDegrees()

    def setLatitude(self, term):
        _parse_degrees(term, self.raw_new_lat)

    def setLongitude(self, term):
        _parse_degrees(term, self.raw_new_lng)

    def commit(self):
        self.raw_lat = self.raw_new_lat
        self.raw_lng = self.raw_new_lng
        self._last_commit_time = time.ticks_ms()
        self.valid = self.updated = True

    def rawLat(self):
        """:returns: RawDegrees, raw latitude value"""
        self.updated = False
        return self.raw_lat

    def rawLng(self):
        """:returns: RawDegrees, raw longitude value"""
        self.updated = False
        return self.raw_lng

    def lat(self):
        """:returns: float, latitude in signed decimal degrees"""
        self.updated = False
        ret = self.raw_lat.deg + self.raw_lat.billionths / 1000000000.0
        return -ret if self.raw_lat.negative else ret

    def lng(self):
        """:returns: float, longitude in signed decimal degrees"""
        self.updated = False
        ret = self.raw_lng.deg + self.raw_lng.billionths / 1000000000.0
        return -ret if self.raw_lng.negative else ret


class NMEADate(_NMEAField):
    """Decoded date (DDMMYY) from GPRMC sentences."""

    def __init__(self):
        super().__init__()
        self._date = 0
        self._new_date = 0

    def setDate(self, term):
        self._new_date = _atol(term)

    def commit(self):
        self._date = self._new_date
        self._last_commit_time = time.ticks_ms()
        self.valid = self.updated = True

    def value(self):
        """:returns: int, raw date value as DDMMYY"""
        self.updated = False
        return self._date

    def year(self):
        """:returns: int, 4-digit year"""
        self.updated = False
        return (self._date % 100) + 2000

    def month(self):
        """:returns: int, month 1-12"""
        self.updated = False
        return (self._date // 100) % 100

    def day(self):
        """:returns: int, day of month 1-31"""
        self.updated = False
        return self._date // 10000


class NMEATime(_NMEAField):
    """Decoded UTC time (HHMMSS.cc) from GPRMC/GPGGA sentences."""

    def __init__(self):
        super().__init__()
        self._time = 0
        self._new_time = 0

    def setTime(self, term):
        self._new_time = _parse_decimal(term)

    def commit(self):
        self._time = self._new_time
        self._last_commit_time = time.ticks_ms()
        self.valid = self.updated = True

    def value(self):
        """:returns: int, raw time value as HHMMSScc"""
        self.updated = False
        return self._time

    def hour(self):
        """:returns: int, hour 0-23 (UTC)"""
        self.updated = False
        return self._time // 1000000

    def minute(self):
        """:returns: int, minute 0-59"""
        self.updated = False
        return (self._time // 10000) % 100

    def second(self):
        """:returns: int, second 0-59"""
        self.updated = False
        return (self._time // 100) % 100

    def centisecond(self):
        """:returns: int, centisecond 0-99"""
        self.updated = False
        return self._time % 100


class NMEADecimal(_NMEAField):
    """Base for decoded fixed-point values scaled by 100 (speed, course, altitude, HDOP)."""

    def __init__(self):
        super().__init__()
        self._val = 0
        self._newval = 0

    def set(self, term):
        self._newval = _parse_decimal(term)

    def commit(self):
        self._val = self._newval
        self._last_commit_time = time.ticks_ms()
        self.valid = self.updated = True

    def value(self):
        """:returns: int, raw value * 100"""
        self.updated = False
        return self._val


class NMEASpeed(NMEADecimal):
    """Decoded ground speed from GPRMC sentences."""

    def knots(self):
        """:returns: float, speed in knots"""
        return self.value() / 100.0

    def mph(self):
        """:returns: float, speed in miles per hour"""
        return _MPH_PER_KNOT * self.value() / 100.0

    def mps(self):
        """:returns: float, speed in meters per second"""
        return _MPS_PER_KNOT * self.value() / 100.0

    def kmph(self):
        """:returns: float, speed in kilometers per hour"""
        return _KMPH_PER_KNOT * self.value() / 100.0


class NMEACourse(NMEADecimal):
    """Decoded course over ground from GPRMC sentences."""

    def deg(self):
        """:returns: float, course in degrees (0-360, 0=North)"""
        return self.value() / 100.0


class NMEAAltitude(NMEADecimal):
    """Decoded altitude from GPGGA sentences."""

    def meters(self):
        """:returns: float, altitude in meters"""
        return self.value() / 100.0

    def miles(self):
        """:returns: float, altitude in miles"""
        return _MILES_PER_METER * self.value() / 100.0

    def kilometers(self):
        """:returns: float, altitude in kilometers"""
        return _KM_PER_METER * self.value() / 100.0

    def feet(self):
        """:returns: float, altitude in feet"""
        return _FEET_PER_METER * self.value() / 100.0


class NMEAHDOP(NMEADecimal):
    """Decoded horizontal dilution of precision from GPGGA sentences."""

    def hdop(self):
        """:returns: float, HDOP value (lower is better precision)"""
        return self.value() / 100.0


class NMEAInteger(_NMEAField):
    """Decoded plain integer value (used for satellite count)."""

    def __init__(self):
        super().__init__()
        self._val = 0
        self._newval = 0

    def set(self, term):
        self._newval = _atol(term)

    def commit(self):
        self._val = self._newval
        self._last_commit_time = time.ticks_ms()
        self.valid = self.updated = True

    def value(self):
        """:returns: int, decoded value"""
        self.updated = False
        return self._val


class GNSS:
    """
    Driver for the Soldered L86-M33 GNSS breakout in native UART mode.

    Feed raw bytes from the module's UART into encode() as they arrive; decoded
    fields are exposed as attributes (location, date, time, speed, course,
    altitude, satellites, hdop), mirroring the Arduino TinyGPS++ based library.
    """

    def __init__(self, uart_id, tx, rx, baudrate=9600):
        """
        Initialize the GNSS module over a hardware UART.

        :param uart_id: int, UART peripheral id (board-specific)
        :param tx: int, TX pin number (connect to the GNSS module's RX pin)
        :param rx: int, RX pin number (connect to the GNSS module's TX pin)
        :param baudrate: int, UART baudrate, L86-M33 default is 9600
        """
        self.uart = UART(uart_id, baudrate=baudrate, tx=Pin(tx), rx=Pin(rx))

        self.location = NMEALocation()
        self.date = NMEADate()
        self.time = NMEATime()
        self.speed = NMEASpeed()
        self.course = NMEACourse()
        self.altitude = NMEAAltitude()
        self.satellites = NMEAInteger()
        self.hdop = NMEAHDOP()

        self._parity = 0
        self._is_checksum_term = False
        self._term_chars = []
        self._cur_sentence_type = _SENTENCE_OTHER
        self._cur_term_number = 0
        self._sentence_has_fix = False

        self._chars_processed = 0
        self._sentences_with_fix = 0
        self._failed_checksum = 0
        self._passed_checksum = 0

    def encode(self, c):
        """
        Feed one received byte into the NMEA parser.

        :param c: int, raw byte value read from the GNSS UART
        :returns: bool, True if a full sentence was just decoded and passed its checksum test
        """
        self._chars_processed += 1

        if c == 44:  # ','
            self._parity ^= c
            return self._onTermComplete(c)
        elif c == 13 or c == 10 or c == 42:  # '\r', '\n', '*'
            return self._onTermComplete(c)
        elif c == 36:  # '$'
            self._cur_term_number = 0
            self._term_chars = []
            self._parity = 0
            self._cur_sentence_type = _SENTENCE_OTHER
            self._is_checksum_term = False
            self._sentence_has_fix = False
            return False
        else:
            if len(self._term_chars) < _MAX_FIELD_SIZE:
                self._term_chars.append(chr(c))
            if not self._is_checksum_term:
                self._parity ^= c
            return False

    def charsProcessed(self):
        """:returns: int, total number of bytes fed into encode()"""
        return self._chars_processed

    def sentencesWithFix(self):
        """:returns: int, number of RMC/GGA sentences decoded that carried a valid fix"""
        return self._sentences_with_fix

    def failedChecksum(self):
        """:returns: int, number of sentences that failed the checksum test"""
        return self._failed_checksum

    def passedChecksum(self):
        """:returns: int, number of sentences that passed the checksum test"""
        return self._passed_checksum

    def sendCommand(self, cmd):
        """
        Send a raw PMTK command string to the GNSS module. Checksum and line ending are added
        automatically.

        :param cmd: str, command string without checksum, e.g. "$PMTK225,8"
        :returns: None
        """
        self.uart.write(cmd)
        self._sendChecksum(cmd)

    @staticmethod
    def parseDecimal(term):
        """
        Parse a signed NMEA numeric field with up to 2 decimal digits (-xxxx.yy).

        :param term: str, raw NMEA field
        :returns: int, value scaled by 100
        """
        return _parse_decimal(term)

    @staticmethod
    def parseDegrees(term, deg):
        """
        Parse an NMEA DDMM.MMMM coordinate field into a RawDegrees object, in place.

        :param term: str, raw NMEA field
        :param deg: RawDegrees, object to fill
        :returns: None
        """
        _parse_degrees(term, deg)

    @staticmethod
    def distanceBetween(lat1, lon1, lat2, lon2):
        """
        Great-circle distance between two signed decimal-degree positions.

        :param lat1: float, latitude of point 1
        :param lon1: float, longitude of point 1
        :param lat2: float, latitude of point 2
        :param lon2: float, longitude of point 2
        :returns: float, distance in meters
        """
        delta = math.radians(lon1 - lon2)
        sdlong = math.sin(delta)
        cdlong = math.cos(delta)
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)
        slat1 = math.sin(lat1)
        clat1 = math.cos(lat1)
        slat2 = math.sin(lat2)
        clat2 = math.cos(lat2)
        delta = (clat1 * slat2) - (slat1 * clat2 * cdlong)
        delta = delta * delta
        delta += (clat2 * sdlong) * (clat2 * sdlong)
        delta = math.sqrt(delta)
        denom = (slat1 * slat2) + (clat1 * clat2 * cdlong)
        delta = math.atan2(delta, denom)
        return delta * 6372795

    @staticmethod
    def courseTo(lat1, lon1, lat2, lon2):
        """
        Course in degrees (North=0) from position 1 to position 2.

        :param lat1: float, latitude of point 1
        :param lon1: float, longitude of point 1
        :param lat2: float, latitude of point 2
        :param lon2: float, longitude of point 2
        :returns: float, course in degrees
        """
        dlon = math.radians(lon2 - lon1)
        lat1 = math.radians(lat1)
        lat2 = math.radians(lat2)
        a1 = math.sin(dlon) * math.cos(lat2)
        a2 = math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        a2 = math.cos(lat1) * math.sin(lat2) - a2
        a2 = math.atan2(a1, a2)
        if a2 < 0.0:
            a2 += 2 * math.pi
        return math.degrees(a2)

    @staticmethod
    def cardinal(course):
        """
        Convert a course in degrees into a 16-point cardinal direction string.

        :param course: float, course in degrees
        :returns: str, e.g. "N", "NNE", "NE", ...
        """
        directions = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")
        direction = int((course + 11.25) / 22.5)
        return directions[direction % 16]

    def _onTermComplete(self, c):
        term = ''.join(self._term_chars)
        is_valid_sentence = self._endOfTermHandler(term)
        self._cur_term_number += 1
        self._term_chars = []
        self._is_checksum_term = c == 42
        return is_valid_sentence

    def _endOfTermHandler(self, term):
        if self._is_checksum_term:
            checksum = 16 * self._fromHex(term[0]) + self._fromHex(term[1])
            if checksum == self._parity:
                self._passed_checksum += 1
                if self._sentence_has_fix:
                    self._sentences_with_fix += 1

                if self._cur_sentence_type == _SENTENCE_GPRMC:
                    self.date.commit()
                    self.time.commit()
                    if self._sentence_has_fix:
                        self.location.commit()
                        self.speed.commit()
                        self.course.commit()
                elif self._cur_sentence_type == _SENTENCE_GPGGA:
                    self.time.commit()
                    if self._sentence_has_fix:
                        self.location.commit()
                        self.altitude.commit()
                    self.satellites.commit()
                    self.hdop.commit()

                return True
            else:
                self._failed_checksum += 1
                return False

        if self._cur_term_number == 0:
            if term == "GPRMC" or term == "GNRMC":
                self._cur_sentence_type = _SENTENCE_GPRMC
            elif term == "GPGGA" or term == "GNGGA":
                self._cur_sentence_type = _SENTENCE_GPGGA
            else:
                self._cur_sentence_type = _SENTENCE_OTHER
            return False

        if self._cur_sentence_type != _SENTENCE_OTHER and term:
            t = self._cur_sentence_type
            n = self._cur_term_number
            if n == 1:  # time, both sentence types
                self.time.setTime(term)
            elif t == _SENTENCE_GPRMC and n == 2:  # GPRMC validity
                self._sentence_has_fix = term[0] == 'A'
            elif (t == _SENTENCE_GPRMC and n == 3) or (t == _SENTENCE_GPGGA and n == 2):  # latitude
                self.location.setLatitude(term)
            elif (t == _SENTENCE_GPRMC and n == 4) or (t == _SENTENCE_GPGGA and n == 3):  # N/S
                self.location.raw_new_lat.negative = term[0] == 'S'
            elif (t == _SENTENCE_GPRMC and n == 5) or (t == _SENTENCE_GPGGA and n == 4):  # longitude
                self.location.setLongitude(term)
            elif (t == _SENTENCE_GPRMC and n == 6) or (t == _SENTENCE_GPGGA and n == 5):  # E/W
                self.location.raw_new_lng.negative = term[0] == 'W'
            elif t == _SENTENCE_GPRMC and n == 7:  # speed
                self.speed.set(term)
            elif t == _SENTENCE_GPRMC and n == 8:  # course
                self.course.set(term)
            elif t == _SENTENCE_GPRMC and n == 9:  # date
                self.date.setDate(term)
            elif t == _SENTENCE_GPGGA and n == 6:  # fix quality
                self._sentence_has_fix = term[0] > '0'
            elif t == _SENTENCE_GPGGA and n == 7:  # satellites used
                self.satellites.set(term)
            elif t == _SENTENCE_GPGGA and n == 8:  # HDOP
                self.hdop.set(term)
            elif t == _SENTENCE_GPGGA and n == 9:  # altitude
                self.altitude.set(term)

        return False

    @staticmethod
    def _fromHex(a):
        if 'A' <= a <= 'F':
            return ord(a) - ord('A') + 10
        elif 'a' <= a <= 'f':
            return ord(a) - ord('a') + 10
        else:
            return ord(a) - ord('0')

    def _sendChecksum(self, s):
        checksum = 0
        for ch in s[1:]:
            checksum ^= ord(ch)
        checksum &= 0xFF
        self.uart.write('*')
        self.uart.write(self._intToHexChar(checksum // 16))
        self.uart.write(self._intToHexChar(checksum % 16))
        self.uart.write('\r\n')

    @staticmethod
    def _intToHexChar(c):
        return chr(ord('A') + (c - 10)) if c >= 10 else chr(ord('0') + c)
