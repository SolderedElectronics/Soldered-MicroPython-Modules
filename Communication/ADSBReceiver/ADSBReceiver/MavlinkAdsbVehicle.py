# FILE: MavlinkAdsbVehicle.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Decoded MAVLink ADSB_VEHICLE message (id 246)
# LAST UPDATED: 2026-07-22

# ADSB_VEHICLE "altitude_type" field values.
ADSB_ALTITUDE_TYPE_PRESSURE_QNH = 0
ADSB_ALTITUDE_TYPE_GEOMETRIC = 1

# ADSB_VEHICLE "emitter_type" field values.
ADSB_EMITTER_TYPE_NO_INFO = 0
ADSB_EMITTER_TYPE_LIGHT = 1
ADSB_EMITTER_TYPE_SMALL = 2
ADSB_EMITTER_TYPE_LARGE = 3
ADSB_EMITTER_TYPE_HIGH_VORTEX_LARGE = 4
ADSB_EMITTER_TYPE_HEAVY = 5
ADSB_EMITTER_TYPE_HIGHLY_MANUV = 6
ADSB_EMITTER_TYPE_ROTORCRAFT = 7
ADSB_EMITTER_TYPE_UNASSIGNED = 8
ADSB_EMITTER_TYPE_GLIDER = 9
ADSB_EMITTER_TYPE_LIGHTER_AIR = 10
ADSB_EMITTER_TYPE_PARACHUTE = 11
ADSB_EMITTER_TYPE_ULTRA_LIGHT = 12
ADSB_EMITTER_TYPE_UNASSIGNED2 = 13
ADSB_EMITTER_TYPE_UAV = 14
ADSB_EMITTER_TYPE_SPACE = 15
ADSB_EMITTER_TYPE_UNASSIGNED3 = 16
ADSB_EMITTER_TYPE_EMERGENCY_SURFACE = 17
ADSB_EMITTER_TYPE_SERVICE_SURFACE = 18
ADSB_EMITTER_TYPE_POINT_OBSTACLE = 19

# ADSB_VEHICLE "flags" bitmask.
ADSB_VEHICLE_FLAG_VALID_COORDS = 0x0001
ADSB_VEHICLE_FLAG_VALID_ALTITUDE = 0x0002
ADSB_VEHICLE_FLAG_VALID_HEADING = 0x0004
ADSB_VEHICLE_FLAG_VALID_VELOCITY = 0x0008
ADSB_VEHICLE_FLAG_VALID_CALLSIGN = 0x0010
ADSB_VEHICLE_FLAG_VALID_SQUAWK = 0x0020
ADSB_VEHICLE_FLAG_SIMULATED = 0x0040
ADSB_VEHICLE_FLAG_VERTICAL_VELOCITY_VALID = 0x0080
ADSB_VEHICLE_FLAG_BARO_VALID = 0x0100
ADSB_VEHICLE_FLAG_SOURCE_UAT = 0x8000


class MavlinkAdsbVehicle:
    """Decoded MAVLink ADSB_VEHICLE message (id 246): one aircraft's state,
    as the module reports it over MAVLink instead of CSV.
    """

    def __init__(self):
        self.icaoAddress = 0
        self.lat = 0  # degrees * 1e7
        self.lon = 0  # degrees * 1e7
        self.altitudeType = ADSB_ALTITUDE_TYPE_PRESSURE_QNH
        self.altitude = 0  # mm
        self.heading = 0  # centidegrees
        self.horVelocity = 0  # cm/s
        self.verVelocity = 0  # cm/s, positive up
        self.callsign = ""
        self.emitterType = ADSB_EMITTER_TYPE_NO_INFO
        self.tslc = 0  # seconds since last contact with this aircraft
        self.flags = 0
        self.squawk = 0

    def latDegrees(self):
        """
        :returns: float, latitude in degrees
        """
        return self.lat / 1e7

    def lonDegrees(self):
        """
        :returns: float, longitude in degrees
        """
        return self.lon / 1e7

    def altitudeMeters(self):
        """
        :returns: float, altitude in meters
        """
        return self.altitude / 1000.0

    def hasValidCoords(self):
        """
        :returns: bool
        """
        return bool(self.flags & ADSB_VEHICLE_FLAG_VALID_COORDS)

    def hasValidAltitude(self):
        """
        :returns: bool
        """
        return bool(self.flags & ADSB_VEHICLE_FLAG_VALID_ALTITUDE)

    def hasValidHeading(self):
        """
        :returns: bool
        """
        return bool(self.flags & ADSB_VEHICLE_FLAG_VALID_HEADING)

    def hasValidVelocity(self):
        """
        :returns: bool
        """
        return bool(self.flags & ADSB_VEHICLE_FLAG_VALID_VELOCITY)

    def hasValidCallsign(self):
        """
        :returns: bool
        """
        return bool(self.flags & ADSB_VEHICLE_FLAG_VALID_CALLSIGN)

    def hasValidSquawk(self):
        """
        :returns: bool
        """
        return bool(self.flags & ADSB_VEHICLE_FLAG_VALID_SQUAWK)

    def isSimulated(self):
        """
        :returns: bool
        """
        return bool(self.flags & ADSB_VEHICLE_FLAG_SIMULATED)

    def hasValidVerticalVelocity(self):
        """
        :returns: bool
        """
        return bool(self.flags & ADSB_VEHICLE_FLAG_VERTICAL_VELOCITY_VALID)

    def hasValidBaro(self):
        """
        :returns: bool
        """
        return bool(self.flags & ADSB_VEHICLE_FLAG_BARO_VALID)

    def isFromUat(self):
        """
        :returns: bool
        """
        return bool(self.flags & ADSB_VEHICLE_FLAG_SOURCE_UAT)
