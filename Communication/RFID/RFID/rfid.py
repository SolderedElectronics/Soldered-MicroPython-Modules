# FILE: rfid.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: A MicroPython module for the RFID 125kHz reader board
# LAST UPDATED: 2025-10-06
from machine import UART, Pin, I2C
import time


class RFID:
    SERIAL_TIMEOUT_MS = 100

    # I2C Register addresses
    REG_AVAILABLE = 0
    REG_TAG_ID = 1
    REG_RAW_DATA = 2
    REG_CLEAR = 3

    def __init__(
        self, i2c=None, i2c_address=0x30, rx_pin=None, tx_pin=None, baud_rate=9600
    ):
        """
        Initialize RFID reader
        Priority: I2C mode if i2c provided, otherwise UART mode
        """
        if i2c is not None:
            # I2C mode (priority)
            self.native = False
            self.i2c = i2c
            self.address = i2c_address
            self.tag_id = 0
            self.rfid_raw = 0
        elif rx_pin is not None and tx_pin is not None:
            # UART mode
            self.native = True
            self.rfid_serial = UART(
                1, baudrate=baud_rate, rx=Pin(rx_pin), tx=Pin(tx_pin)
            )
            self.rx_pin = rx_pin
            self.tx_pin = tx_pin
            self.baud_rate = baud_rate
            self.tag_id = 0
            self.rfid_raw = 0
        else:
            raise ValueError("Either I2C object or RX/TX pins must be provided")

    def checkHW(self):
        """Check if hardware is responding"""
        if not self.native:
            # I2C mode - ping the module on its I2C address
            try:
                self.i2c.writeto(self.address, b"")
                # Clear all previous data from the RFID reader
                self.clear()
                return True
            except OSError:
                return False
        else:
            # UART mode
            self.rfid_serial.write("#rfping\n")
            time.sleep_ms(15)

            serial_data = self.getSerialData(25, self.SERIAL_TIMEOUT_MS)
            if serial_data and "#hello" in serial_data:
                return True
            return False

    def available(self):
        """Check if there is new RFID data available"""
        if not self.native:
            # I2C mode
            try:
                # Set register address to REG_AVAILABLE (0)
                self.i2c.writeto(self.address, bytes([self.REG_AVAILABLE]))
                # Read 1 byte
                data = self.i2c.readfrom(self.address, 1)
                return bool(data[0])
            except OSError:
                return False
        else:
            # UART mode
            available_flag = False
            serial_data = self.getSerialData(30, self.SERIAL_TIMEOUT_MS)

            if serial_data:
                tag_id_start = serial_data.find("$")
                tag_raw_start = serial_data.find("&")

                if tag_id_start != -1 and tag_raw_start != -1:
                    tag_id_str = serial_data[tag_id_start + 1 : tag_raw_start]
                    raw_str = serial_data[tag_raw_start + 1 :]

                    try:
                        self.tag_id = int(tag_id_str)
                        self.rfid_raw = self.getUint64(raw_str)

                        if self.tag_id and self.rfid_raw:
                            available_flag = True
                    except ValueError:
                        pass

            return available_flag

    def getId(self):
        """Get the RFID Tag ID number and clear it after reading"""
        if not self.native:
            # I2C mode
            try:
                # Set register address to REG_TAG_ID (1)
                self.i2c.writeto(self.address, bytes([self.REG_TAG_ID]))
                # Read 4 bytes for tag ID
                data = self.i2c.readfrom(self.address, 4)
                # Convert bytes to uint32 (little endian)
                tag_id = int.from_bytes(data, "little")
                return tag_id
            except OSError:
                return 0
        else:
            # UART mode
            tag_id = self.tag_id
            self.tag_id = 0
            return tag_id

    def getRaw(self):
        """Get the RFID RAW data with headers, RAW data, parity bits, etc."""
        if not self.native:
            # I2C mode
            try:
                # Set register address to REG_RAW_DATA (2)
                self.i2c.writeto(self.address, bytes([self.REG_RAW_DATA]))
                # Read 8 bytes for raw RFID data
                data = self.i2c.readfrom(self.address, 8)
                # Convert bytes to uint64 (little endian)
                rfid_raw = int.from_bytes(data, "little")
                return rfid_raw
            except OSError:
                return 0
        else:
            # UART mode
            rfid_raw = self.rfid_raw
            self.rfid_raw = 0
            return rfid_raw

    def clear(self):
        """Clear all previous data from the RFID reader (I2C mode only)"""
        if not self.native:
            try:
                # Set register address to REG_CLEAR (3) to clear data
                self.i2c.writeto(self.address, bytes([self.REG_CLEAR]))
            except OSError:
                pass

    def getSerialData(self, max_length, timeout_ms):
        """Get data from serial with timeout"""
        if not self.native:
            return None

        timeout = time.ticks_ms()
        data = bytearray()

        while time.ticks_diff(time.ticks_ms(), timeout) < timeout_ms:
            if self.rfid_serial.any():
                char = self.rfid_serial.read(1)
                if char:
                    data.extend(char)
                    timeout = time.ticks_ms()  # Reset timeout on new data

                if len(data) >= max_length:
                    break

        return data.decode("utf-8", "ignore") if data else None

    def getUint64(self, hex_string):
        """Convert HEX string to 64-bit integer"""
        try:
            # Clean the hex string - remove any non-hex characters
            hex_string = "".join(c for c in hex_string if c in "0123456789ABCDEFabcdef")
            hex_string = hex_string.upper()

            # Ensure we have exactly 16 characters for 64-bit
            # If shorter, pad with zeros; if longer, truncate
            if len(hex_string) < 16:
                hex_string = hex_string + "0" * (16 - len(hex_string))
            else:
                hex_string = hex_string[:16]

            return int(hex_string, 16)
        except (ValueError, AttributeError):
            return 0

    def printHex64(self, number):
        """Print 64-bit number in HEX format"""
        hex_str = "{:016X}".format(number & 0xFFFFFFFFFFFFFFFF)
        print(hex_str)

    def hexToInt(self, char):
        """Convert HEX char to integer (0-15)"""
        char = char.upper()
        if "0" <= char <= "9":
            return ord(char) - ord("0")
        elif "A" <= char <= "F":
            return ord(char) - ord("A") + 10
        return 0

    def intToHex(self, number):
        """Convert integer (0-15) to HEX char"""
        number &= 0x0F
        if 0 <= number <= 9:
            return chr(ord("0") + number)
        elif 10 <= number <= 15:
            return chr(ord("A") + number - 10)
        return "0"
