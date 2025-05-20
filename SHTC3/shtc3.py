from machine import I2C, Pin
import time

# I2C address
I2C_ADDR = 0x70

# Sensor commands
SHTC3_SLEEP = 0xB098
SHTC3_WAKEUP = 0x3517
SHTC3_RESET = 0x805D
SHTC3_ID = 0xEFC8
SHTC3_READ = 0x7CA2     # Normal power
SHTC3_READ_LP = 0x6458  # Low power

# Scaling constants
H_K = 0.001525878906
T_K = 0.002670288086
T_MIN = 45.0

class SHTC3:
    def __init__(self, i2c: I2C):
        self.i2c = i2c
        self._t = 0
        self._h = 0

    def crc8(self, data):
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = ((crc << 1) ^ 0x31) if (crc & 0x80) else (crc << 1)
                crc &= 0xFF
        return crc

    def check_crc(self, data):
        return self.crc8(data[:2]) == data[2]

    def twi_command(self, cmd, stop=True):
        try:
            self.i2c.writeto(I2C_ADDR, bytes([cmd >> 8, cmd & 0xFF]), stop)
            return True
        except OSError:
            return False

    def twi_transfer(self, cmd, length, pause_ms=0):
        if not self.twi_command(cmd, stop=False):
            return None
        if pause_ms > 0:
            time.sleep_ms(pause_ms)
        try:
            data = self.i2c.readfrom(I2C_ADDR, length)
            return data if len(data) == length else None
        except OSError:
            return None

    def wakeup(self):
        return self.twi_command(SHTC3_WAKEUP)

    def reset(self):
        return self.twi_command(SHTC3_RESET)

    def sleep(self):
        return self.twi_command(SHTC3_SLEEP)

    def begin(self, do_sample=True):
        time.sleep_us(240)
        if not self.wakeup():
            return False

        id_data = self.twi_transfer(SHTC3_ID, 3, pause_ms=1)
        if not id_data or not self.check_crc(id_data):
            return False

        sig_valid = (id_data[0] & 0b00001000) and ((id_data[1] & 0b00111111) == 0b00000111)
        if not sig_valid:
            return False

        if not self.reset():
            return False

        if do_sample and not self.sample():
            return False

        return self.sleep()

    def sample(self, readcmd=SHTC3_READ, pause=15):
        if not self.wakeup():
            return False
        data = self.twi_transfer(readcmd, 6, pause)
        self.sleep()
        if not data or not self.check_crc(data) or not self.check_crc(data[3:]):
            return False

        self._t = (data[0] << 8) | data[1]
        self._h = (data[3] << 8) | data[4]
        return True

    def readTemperature(self):
        return (self._t * T_K) - T_MIN

    def readHumidity(self):
        return self._h * H_K



