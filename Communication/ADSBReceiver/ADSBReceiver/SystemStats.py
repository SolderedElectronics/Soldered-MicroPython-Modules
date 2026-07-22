# FILE: SystemStats.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: Decoded system CSV "#S:" statistics message
# LAST UPDATED: 2026-07-22


class SystemStats:
    """Decoded system CSV "#S:" statistics message."""

    def __init__(self):
        self.cpuLoad = 0.0  # percent
        self.uptime = 0
        self.crc = 0
        self.crcValid = False
