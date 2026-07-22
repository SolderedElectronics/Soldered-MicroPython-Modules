# FILE: AdsbAircraft.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Decoded ADS-B CSV "#A:" aircraft state vector message
# LAST UPDATED: 2026-07-22

# ADS-B aircraft FLAGS bitfield.
FLAG_PLANE_ON_THE_GROUND = 0x0001
FLAG_PLANE_IS_MILITARY = 0x0002
FLAG_PLANE_UPDATE_ALTITUDE_BARO = 0x0100
FLAG_PLANE_UPDATE_POSITION = 0x0200
FLAG_PLANE_UPDATE_TRACK = 0x0400
FLAG_PLANE_UPDATE_VELO_H = 0x0800
FLAG_PLANE_UPDATE_VELO_V = 0x1000
FLAG_PLANE_UPDATE_ALTITUDE_GEO = 0x2000


class AdsbAircraft:
    """Decoded ADS-B CSV aircraft state vector.

    Any field the module didn't have data for is left at its default, with
    the corresponding has* flag False.
    """

    def __init__(self):
        self.icao = ""  # ICAO 24-bit address, hex string
        self.flags = 0
        self.callsign = ""
        self.squawk = ""
        self.hasPosition = False
        self.lat = 0.0
        self.lon = 0.0
        self.hasAltBaro = False
        self.altBaro = 0  # feet
        self.hasTrack = False
        self.track = 0.0  # degrees [0,360)
        self.hasVelH = False
        self.velH = 0.0  # knots
        self.hasVelV = False
        self.velV = 0  # ft/min
        self.hasSigS = False
        self.sigS = 0  # dBm
        self.hasSigQ = False
        self.sigQ = 0  # dB
        self.fps = 0  # raw Mode-S frames received last second
        self.hasNicNac = False
        self.nicNac = 0  # raw NIC/NAC bitfield
        self.hasAltGeo = False
        self.altGeo = 0  # feet
        self.hasEcat = False
        self.ecat = 0  # emitter category code
        self.crc = 0
        self.crcValid = False

    def onGround(self):
        """
        :returns: bool, True if aircraft is on the ground
        """
        return bool(self.flags & FLAG_PLANE_ON_THE_GROUND)

    def isMilitary(self):
        """
        :returns: bool, True if aircraft is flagged military
        """
        return bool(self.flags & FLAG_PLANE_IS_MILITARY)

    def updatedAltBaro(self):
        """
        :returns: bool, True if this report updated barometric altitude
        """
        return bool(self.flags & FLAG_PLANE_UPDATE_ALTITUDE_BARO)

    def updatedPosition(self):
        """
        :returns: bool, True if this report updated position
        """
        return bool(self.flags & FLAG_PLANE_UPDATE_POSITION)

    def updatedTrack(self):
        """
        :returns: bool, True if this report updated track
        """
        return bool(self.flags & FLAG_PLANE_UPDATE_TRACK)

    def updatedVeloH(self):
        """
        :returns: bool, True if this report updated horizontal velocity
        """
        return bool(self.flags & FLAG_PLANE_UPDATE_VELO_H)

    def updatedVeloV(self):
        """
        :returns: bool, True if this report updated vertical velocity
        """
        return bool(self.flags & FLAG_PLANE_UPDATE_VELO_V)

    def updatedAltGeo(self):
        """
        :returns: bool, True if this report updated geometric altitude
        """
        return bool(self.flags & FLAG_PLANE_UPDATE_ALTITUDE_GEO)
