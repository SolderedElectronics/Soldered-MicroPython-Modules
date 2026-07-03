# FILE: lmp91000.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython driver for LMP91000 analog frontend (helper for ElectrochemicalGasSensor)
# LAST UPDATED: 2026-05-21

_LMP_ADDR = 0x48
_STATUS_REG = 0x00
_LOCK_REG = 0x01
_TIACN_REG = 0x10
_REFCN_REG = 0x11
_MODECN_REG = 0x12

_WRITE_LOCK = 0x01
_WRITE_UNLOCK = 0x00
_READY = 0x01


class LMP91000:
    """Analog frontend for electrochemical sensors over I2C. Used internally by ElectrochemicalGasSensor."""

    def __init__(self, i2c):
        self._i2c = i2c

    def write(self, reg, data):
        """Write data byte to register, return read-back value."""
        self._i2c.writeto(_LMP_ADDR, bytes([reg, data]))
        return self.read(reg)

    def read(self, reg):
        """Read one byte from register."""
        self._i2c.writeto(_LMP_ADDR, bytes([reg]))
        return self._i2c.readfrom(_LMP_ADDR, 1)[0]

    def status(self):
        """Return status register. 0x01 = ready."""
        return self.read(_STATUS_REG)

    def lock(self):
        """Lock configuration registers."""
        return self.write(_LOCK_REG, _WRITE_LOCK)

    def unlock(self):
        """Unlock configuration registers."""
        return self.write(_LOCK_REG, _WRITE_UNLOCK)

    def configure(self, tiacn, refcn, modecn):
        """Configure TIA, reference, and mode registers. Returns 1 on success, 0 if not ready."""
        if self.status() == _READY:
            self.unlock()
            self.write(_TIACN_REG, tiacn)
            self.write(_REFCN_REG, refcn)
            self.write(_MODECN_REG, modecn)
            self.lock()
            return 1
        return 0
