# FILE: AdsbStats.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Decoded ADS-B CSV "#AS:" statistics message
# LAST UPDATED: 2026-07-22


class AdsbStats:
    """Decoded ADS-B CSV "#AS:" statistics message."""

    def __init__(self):
        self.fpss = 0  # all received Mode-S frames per second
        self.fpsac = 0  # all received Mode-A/C frames per second
        self.calib = 0.0  # real uC frequency based on GNSS module (PPS)
        self.crc = 0
        self.crcValid = False
