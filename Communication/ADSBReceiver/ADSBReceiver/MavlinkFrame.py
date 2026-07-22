# FILE: MavlinkFrame.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: One raw MAVLink v1 or v2 frame, whatever its message ID
# LAST UPDATED: 2026-07-22


class MavlinkFrame:
    """One raw MAVLink v1 or v2 frame, whatever its message ID.

    crcValid is only ever True for message IDs this library knows the CRC_EXTRA
    byte for (currently HEARTBEAT and ADSB_VEHICLE); for anything else it stays
    False even if the frame is actually fine, since the checksum can't be
    verified without that per-message constant.
    """

    def __init__(self):
        self.version = 0  # 1 or 2
        self.sysid = 0
        self.compid = 0
        self.seq = 0
        self.msgid = 0
        self.payload = b""
        self.crcValid = False
