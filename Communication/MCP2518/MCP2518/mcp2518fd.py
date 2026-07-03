# FILE: mcp2518fd.py
# AUTHOR: Fran Fodor @ Soldered
# BRIEF: MicroPython driver for MCP2518FD CAN FD controller via SPI
# WORKS WITH: CAN Bus Breakout: solde.red/333020
# LAST UPDATED: 2026-05-21

from machine import SPI, Pin
import time

# ===========================================================================
# Return codes
# ===========================================================================
CAN_OK = 0
CAN_FAILINIT = 1
CAN_FAILTX = 2
CAN_MSGAVAIL = 3
CAN_NOMSG = 4
CAN_CTRLERROR = 5
CAN_GETTXBFTIMEOUT = 6
CAN_SENDMSGTIMEOUT = 7
CAN_FAIL = 0xFF

# ===========================================================================
# Clock frequencies
# ===========================================================================
MCP2518FD_40MHz = 1
MCP2518FD_20MHz = 2
MCP2518FD_10MHz = 3

# ===========================================================================
# Legacy baud rate constants (passed to begin())
# ===========================================================================
CAN_5KBPS = 1
CAN_10KBPS = 2
CAN_20KBPS = 3
CAN_25KBPS = 4
CAN_31K25BPS = 5
CAN_33KBPS = 6
CAN_40KBPS = 7
CAN_50KBPS = 8
CAN_80KBPS = 9
CAN_83K3BPS = 10
CAN_95KBPS = 11
CAN_100KBPS = 12
CAN_125KBPS = 13
CAN_200KBPS = 14
CAN_250KBPS = 15
CAN_500KBPS = 16
CAN_666KBPS = 17
CAN_800KBPS = 18
CAN_1000KBPS = 19

# Pre-defined CAN FD dual-rate constants: (factor << 24) | arb_bitrate
CAN_125K_500K = (4 << 24) | 125000
CAN_250K_500K = (2 << 24) | 250000
CAN_250K_750K = (3 << 24) | 250000
CAN_250K_1M = (4 << 24) | 250000
CAN_250K_2M = (8 << 24) | 250000
CAN_500K_1M = (2 << 24) | 500000
CAN_500K_2M = (4 << 24) | 500000
CAN_500K_4M = (8 << 24) | 500000
CAN_1000K_4M = (4 << 24) | 1000000
CAN_1000K_8M = (8 << 24) | 1000000

# ===========================================================================
# Operation modes
# ===========================================================================
CAN_NORMAL_MODE = 0x00
CAN_SLEEP_MODE = 0x01
CAN_INTERNAL_LOOPBACK_MODE = 0x02
CAN_LISTEN_ONLY_MODE = 0x03
CAN_CONFIGURATION_MODE = 0x04
CAN_EXTERNAL_LOOPBACK_MODE = 0x05
CAN_CLASSIC_MODE = 0x06
CAN_RESTRICTED_MODE = 0x07
CAN_INVALID_MODE = 0xFF

# ===========================================================================
# SSP modes
# ===========================================================================
CAN_SSP_MODE_OFF = 0
CAN_SSP_MODE_MANUAL = 1
CAN_SSP_MODE_AUTO = 2

# ===========================================================================
# DLC constants
# ===========================================================================
CAN_DLC_0 = 0
CAN_DLC_1 = 1
CAN_DLC_2 = 2
CAN_DLC_3 = 3
CAN_DLC_4 = 4
CAN_DLC_5 = 5
CAN_DLC_6 = 6
CAN_DLC_7 = 7
CAN_DLC_8 = 8
CAN_DLC_12 = 9
CAN_DLC_16 = 10
CAN_DLC_20 = 11
CAN_DLC_24 = 12
CAN_DLC_32 = 13
CAN_DLC_48 = 14
CAN_DLC_64 = 15

# FIFO payload sizes
CAN_PLSIZE_8 = 0
CAN_PLSIZE_12 = 1
CAN_PLSIZE_16 = 2
CAN_PLSIZE_20 = 3
CAN_PLSIZE_24 = 4
CAN_PLSIZE_32 = 5
CAN_PLSIZE_48 = 6
CAN_PLSIZE_64 = 7

# ===========================================================================
# FIFO / filter channel constants
# ===========================================================================
CAN_FIFO_CH0 = 0
CAN_FIFO_CH1 = 1
CAN_FIFO_CH2 = 2
CAN_TXQUEUE_CH0 = 0
CAN_FILTER0 = 0

# ===========================================================================
# Event / interrupt flag constants
# ===========================================================================
CAN_TX_FIFO_NOT_FULL_EVENT = 0x01
CAN_TX_FIFO_HALF_FULL_EVENT = 0x02
CAN_TX_FIFO_EMPTY_EVENT = 0x04
CAN_TX_FIFO_ATTEMPTS_EXHAUSTED_EVENT = 0x10
CAN_TX_FIFO_ALL_EVENTS = 0x17

CAN_RX_FIFO_NOT_EMPTY_EVENT = 0x01
CAN_RX_FIFO_HALF_FULL_EVENT = 0x02
CAN_RX_FIFO_FULL_EVENT = 0x04
CAN_RX_FIFO_OVERFLOW_EVENT = 0x08
CAN_RX_FIFO_ALL_EVENTS = 0x0F

CAN_RX_FIFO_NOT_EMPTY = 0x01

CAN_TX_EVENT = 0x0001
CAN_RX_EVENT = 0x0002
CAN_ALL_EVENTS = 0xFF1F

# ===========================================================================
# Error state constants
# ===========================================================================
CAN_ERROR_FREE_STATE = 0
CAN_ERROR_ALL = 0x3F
CAN_TX_RX_WARNING_STATE = 0x01
CAN_RX_WARNING_STATE = 0x02
CAN_TX_WARNING_STATE = 0x04
CAN_RX_BUS_PASSIVE_STATE = 0x08
CAN_TX_BUS_PASSIVE_STATE = 0x10
CAN_TX_BUS_OFF_STATE = 0x20

# ===========================================================================
# GPIO constants
# ===========================================================================
GPIO_PIN_0 = 0
GPIO_PIN_1 = 1
GPIO_MODE_INT = 0
GPIO_MODE_GPIO = 1
GPIO_OUTPUT = 0
GPIO_INPUT = 1
GPIO_LOW = 0
GPIO_HIGH = 1

# ===========================================================================
# SPI instructions
# ===========================================================================
_INSTR_RESET = 0x00
_INSTR_READ = 0x03
_INSTR_READ_CRC = 0x0B
_INSTR_WRITE = 0x02
_INSTR_WRITE_CRC = 0x0A
_INSTR_WRITE_SAFE = 0x0C

# ===========================================================================
# Register addresses
# ===========================================================================
_REG_CiCON = 0x000
_REG_CiNBTCFG = 0x004
_REG_CiDBTCFG = 0x008
_REG_CiTDC = 0x00C
_REG_CiTBC = 0x010
_REG_CiTSCON = 0x014
_REG_CiVEC = 0x018
_REG_CiINT = 0x01C
_REG_CiINTENABLE = 0x01E
_REG_CiRXIF = 0x020
_REG_CiTXIF = 0x024
_REG_CiRXOVIF = 0x028
_REG_CiTXATIF = 0x02C
_REG_CiTXREQ = 0x030
_REG_CiTREC = 0x034
_REG_CiBDIAG0 = 0x038
_REG_CiBDIAG1 = 0x03C
_REG_CiTEFCON = 0x040
_REG_CiTEFSTA = 0x044
_REG_CiTEFUA = 0x048
_REG_CiFIFOBA = 0x04C
_REG_CiFIFOCON = 0x050
_REG_CiFIFOSTA = 0x054
_REG_CiFIFOUA = 0x058
_FIFO_OFFSET = 12  # 3 registers * 4 bytes
_FIFO_TOTAL_CH = 32
_REG_CiFLTCON = _REG_CiFIFOCON + _FIFO_OFFSET * _FIFO_TOTAL_CH
_REG_CiFLTOBJ = _REG_CiFLTCON + _FIFO_TOTAL_CH
_REG_CiMASK = _REG_CiFLTOBJ + 4
_FILTER_OFFSET = 8  # 2 registers * 4 bytes
_REG_OSC = 0xE00
_REG_IOCON = 0xE04
_REG_CRC_REG = 0xE08
_REG_ECCCON = 0xE0C
_REG_ECCSTA = 0xE10
_REG_DEVID = 0xE14

_RAM_START = 0x400
_RAM_SIZE = 2048

_APP_TX_FIFO = CAN_FIFO_CH2
_APP_RX_FIFO = CAN_FIFO_CH1

_MAX_TXQUEUE_ATTEMPTS = 50
_SPI_CHUNK = 96

# ===========================================================================
# Register reset values
# ===========================================================================
_canControlResetValues = (
    0x04980760,
    0x003E0F0F,
    0x000E0303,
    0x00021000,
    0x00000000,
    0x00000000,
    0x40400040,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00000000,
    0x00200000,
    0x00000000,
    0x00000000,
    0x00000400,
    0x00000000,
    0x00000000,
    0x00000000,
)
_canFifoResetValues = (0x00600400, 0x00000000, 0x00000000)

# ===========================================================================
# CRC-16 lookup table
# ===========================================================================
_crc16_table = (
    0x0000,
    0x8005,
    0x800F,
    0x000A,
    0x801B,
    0x001E,
    0x0014,
    0x8011,
    0x8033,
    0x0036,
    0x003C,
    0x8039,
    0x0028,
    0x802D,
    0x8027,
    0x0022,
    0x8063,
    0x0066,
    0x006C,
    0x8069,
    0x0078,
    0x807D,
    0x8077,
    0x0072,
    0x0050,
    0x8055,
    0x805F,
    0x005A,
    0x804B,
    0x004E,
    0x0044,
    0x8041,
    0x80C3,
    0x00C6,
    0x00CC,
    0x80C9,
    0x00D8,
    0x80DD,
    0x80D7,
    0x00D2,
    0x00F0,
    0x80F5,
    0x80FF,
    0x00FA,
    0x80EB,
    0x00EE,
    0x00E4,
    0x80E1,
    0x00A0,
    0x80A5,
    0x80AF,
    0x00AA,
    0x80BB,
    0x00BE,
    0x00B4,
    0x80B1,
    0x8093,
    0x0096,
    0x009C,
    0x8099,
    0x0088,
    0x808D,
    0x8087,
    0x0082,
    0x8183,
    0x0186,
    0x018C,
    0x8189,
    0x0198,
    0x819D,
    0x8197,
    0x0192,
    0x01B0,
    0x81B5,
    0x81BF,
    0x01BA,
    0x81AB,
    0x01AE,
    0x01A4,
    0x81A1,
    0x01E0,
    0x81E5,
    0x81EF,
    0x01EA,
    0x81FB,
    0x01FE,
    0x01F4,
    0x81F1,
    0x81D3,
    0x01D6,
    0x01DC,
    0x81D9,
    0x01C8,
    0x81CD,
    0x81C7,
    0x01C2,
    0x0140,
    0x8145,
    0x814F,
    0x014A,
    0x815B,
    0x015E,
    0x0154,
    0x8151,
    0x8173,
    0x0176,
    0x017C,
    0x8179,
    0x0168,
    0x816D,
    0x8167,
    0x0162,
    0x8123,
    0x0126,
    0x012C,
    0x8129,
    0x0138,
    0x813D,
    0x8137,
    0x0132,
    0x0110,
    0x8115,
    0x811F,
    0x011A,
    0x810B,
    0x010E,
    0x0104,
    0x8101,
    0x8303,
    0x0306,
    0x030C,
    0x8309,
    0x0318,
    0x831D,
    0x8317,
    0x0312,
    0x0330,
    0x8335,
    0x833F,
    0x033A,
    0x832B,
    0x032E,
    0x0324,
    0x8321,
    0x0360,
    0x8365,
    0x836F,
    0x036A,
    0x837B,
    0x037E,
    0x0374,
    0x8371,
    0x8353,
    0x0356,
    0x035C,
    0x8359,
    0x0348,
    0x834D,
    0x8347,
    0x0342,
    0x03C0,
    0x83C5,
    0x83CF,
    0x03CA,
    0x83DB,
    0x03DE,
    0x03D4,
    0x83D1,
    0x83F3,
    0x03F6,
    0x03FC,
    0x83F9,
    0x03E8,
    0x83ED,
    0x83E7,
    0x03E2,
    0x83A3,
    0x03A6,
    0x03AC,
    0x83A9,
    0x03B8,
    0x83BD,
    0x83B7,
    0x03B2,
    0x0390,
    0x8395,
    0x839F,
    0x039A,
    0x838B,
    0x038E,
    0x0384,
    0x8381,
    0x0280,
    0x8285,
    0x828F,
    0x028A,
    0x829B,
    0x029E,
    0x0294,
    0x8291,
    0x82B3,
    0x02B6,
    0x02BC,
    0x82B9,
    0x02A8,
    0x82AD,
    0x82A7,
    0x02A2,
    0x82E3,
    0x02E6,
    0x02EC,
    0x82E9,
    0x02F8,
    0x82FD,
    0x82F7,
    0x02F2,
    0x02D0,
    0x82D5,
    0x82DF,
    0x02DA,
    0x82CB,
    0x02CE,
    0x02C4,
    0x82C1,
    0x8243,
    0x0246,
    0x024C,
    0x8249,
    0x0258,
    0x825D,
    0x8257,
    0x0252,
    0x0270,
    0x8275,
    0x827F,
    0x027A,
    0x826B,
    0x026E,
    0x0264,
    0x8261,
    0x0220,
    0x8225,
    0x822F,
    0x022A,
    0x823B,
    0x023E,
    0x0234,
    0x8231,
    0x8213,
    0x0216,
    0x021C,
    0x8219,
    0x0208,
    0x820D,
    0x8207,
    0x0202,
)

# ===========================================================================
# Helper functions
# ===========================================================================


def BITRATE(arbitration, factor):
    """Build a CAN FD bitrate value: (factor << 24) | arbitration."""
    return ((factor & 0xFF) << 24) | (arbitration & 0xFFFFF)


def dlc2len(dlc):
    """Convert DLC code to byte count."""
    if dlc <= CAN_DLC_8:
        return dlc
    return {
        CAN_DLC_12: 12,
        CAN_DLC_16: 16,
        CAN_DLC_20: 20,
        CAN_DLC_24: 24,
        CAN_DLC_32: 32,
        CAN_DLC_48: 48,
        CAN_DLC_64: 64,
    }.get(dlc, 0)


def len2dlc(length):
    """Convert byte count to DLC code."""
    if length <= 8:
        return length
    if length <= 12:
        return CAN_DLC_12
    if length <= 16:
        return CAN_DLC_16
    if length <= 20:
        return CAN_DLC_20
    if length <= 24:
        return CAN_DLC_24
    if length <= 32:
        return CAN_DLC_32
    if length <= 48:
        return CAN_DLC_48
    return CAN_DLC_64


def _crc16(data):
    crc = 0xFFFF
    for b in data:
        idx = ((crc >> 8) ^ b) & 0xFF
        crc = ((crc << 8) ^ _crc16_table[idx]) & 0xFFFF
    return crc


# ===========================================================================
# MCP2518FD driver
# ===========================================================================


class MCP2518FD:
    """
    MicroPython driver for the MCP2518FD CAN FD controller.
    Communicates over SPI. CS pin is controlled manually.
    """

    def __init__(self, cs_pin, spi=None, spi_id=1, baudrate=4000000):
        """
        :param cs_pin:   GPIO pin number for SPI chip select (active low)
        :param spi:      Initialized machine.SPI object (optional)
        :param spi_id:   SPI bus ID used when spi is None
        :param baudrate: SPI clock speed when spi is None
        """
        self._cs = Pin(cs_pin, Pin.OUT, value=1)
        if spi is not None:
            self._spi = spi
        else:
            self._spi = SPI(
                spi_id, baudrate=baudrate, polarity=0, phase=0, firstbit=SPI.MSB
            )

        self._mode = CAN_CLASSIC_MODE

        # Bit time calculation state
        self._sys_clock = 0
        self._data_factor = 0
        self._brp = 0
        self._arb_ps1 = 0
        self._arb_ps2 = 0
        self._arb_sjw = 0
        self._data_ps1 = 0
        self._data_ps2 = 0
        self._data_sjw = 0
        self._tdco = 0

        # Last received message state
        self.can_id = 0
        self.ext_flg = 0
        self.rtr = 0

    # -----------------------------------------------------------------------
    # Low-level SPI primitives
    # -----------------------------------------------------------------------

    def _transfer(self, tx):
        rx = bytearray(len(tx))
        self._cs.value(0)
        self._spi.write_readinto(bytes(tx), rx)
        self._cs.value(1)
        return rx

    def _read_byte(self, addr):
        rx = self._transfer(
            bytes([(_INSTR_READ << 4) | ((addr >> 8) & 0xF), addr & 0xFF, 0x00])
        )
        return rx[2]

    def _write_byte(self, addr, val):
        self._transfer(
            bytes([(_INSTR_WRITE << 4) | ((addr >> 8) & 0xF), addr & 0xFF, val & 0xFF])
        )

    def _read_word(self, addr):
        rx = self._transfer(
            bytes([(_INSTR_READ << 4) | ((addr >> 8) & 0xF), addr & 0xFF, 0, 0, 0, 0])
        )
        return rx[2] | (rx[3] << 8) | (rx[4] << 16) | (rx[5] << 24)

    def _write_word(self, addr, val):
        val &= 0xFFFFFFFF
        self._transfer(
            bytes(
                [
                    (_INSTR_WRITE << 4) | ((addr >> 8) & 0xF),
                    addr & 0xFF,
                    val & 0xFF,
                    (val >> 8) & 0xFF,
                    (val >> 16) & 0xFF,
                    (val >> 24) & 0xFF,
                ]
            )
        )

    def _read_half_word(self, addr):
        rx = self._transfer(
            bytes([(_INSTR_READ << 4) | ((addr >> 8) & 0xF), addr & 0xFF, 0, 0])
        )
        return rx[2] | (rx[3] << 8)

    def _write_half_word(self, addr, val):
        self._transfer(
            bytes(
                [
                    (_INSTR_WRITE << 4) | ((addr >> 8) & 0xF),
                    addr & 0xFF,
                    val & 0xFF,
                    (val >> 8) & 0xFF,
                ]
            )
        )

    def _read_byte_array(self, addr, n):
        tx = bytearray(n + 2)
        tx[0] = (_INSTR_READ << 4) | ((addr >> 8) & 0xF)
        tx[1] = addr & 0xFF
        rx = self._transfer(tx)
        return bytes(rx[2:])

    def _write_byte_array(self, addr, data):
        tx = bytearray(2 + len(data))
        tx[0] = (_INSTR_WRITE << 4) | ((addr >> 8) & 0xF)
        tx[1] = addr & 0xFF
        tx[2:] = data
        self._transfer(tx)

    def _read_word_array(self, addr, n_words):
        raw = self._read_byte_array(addr, n_words * 4)
        words = []
        for i in range(n_words):
            o = i * 4
            words.append(
                raw[o] | (raw[o + 1] << 8) | (raw[o + 2] << 16) | (raw[o + 3] << 24)
            )
        return words

    def _write_word_array(self, addr, words):
        buf = bytearray(len(words) * 4)
        for i, w in enumerate(words):
            o = i * 4
            buf[o] = w & 0xFF
            buf[o + 1] = (w >> 8) & 0xFF
            buf[o + 2] = (w >> 16) & 0xFF
            buf[o + 3] = (w >> 24) & 0xFF
        self._write_byte_array(addr, buf)

    def _write_byte_safe(self, addr, val):
        tx = bytearray(5)
        tx[0] = (_INSTR_WRITE_SAFE << 4) | ((addr >> 8) & 0xF)
        tx[1] = addr & 0xFF
        tx[2] = val & 0xFF
        crc = _crc16(tx[:3])
        tx[3] = (crc >> 8) & 0xFF
        tx[4] = crc & 0xFF
        self._transfer(tx)

    def _write_word_safe(self, addr, val):
        tx = bytearray(8)
        tx[0] = (_INSTR_WRITE_SAFE << 4) | ((addr >> 8) & 0xF)
        tx[1] = addr & 0xFF
        tx[2] = val & 0xFF
        tx[3] = (val >> 8) & 0xFF
        tx[4] = (val >> 16) & 0xFF
        tx[5] = (val >> 24) & 0xFF
        crc = _crc16(tx[:6])
        tx[6] = (crc >> 8) & 0xFF
        tx[7] = crc & 0xFF
        self._transfer(tx)

    # -----------------------------------------------------------------------
    # Device init helpers
    # -----------------------------------------------------------------------

    def _reset(self):
        self._transfer(bytes([(_INSTR_RESET << 4) & 0xFF, 0x00]))
        time.sleep_ms(10)

    def _ecc_enable(self):
        d = self._read_byte(_REG_ECCCON)
        self._write_byte(_REG_ECCCON, d | 0x01)

    def _ram_init(self, val=0xFF):
        chunk = bytes([val] * _SPI_CHUNK)
        addr = _RAM_START
        for _ in range(_RAM_SIZE // _SPI_CHUNK):
            self._write_byte_array(addr, chunk)
            addr += _SPI_CHUNK

    # -----------------------------------------------------------------------
    # CAN controller configuration
    # -----------------------------------------------------------------------

    def _configure(self, iso_crc=1, store_in_tef=0):
        word = _canControlResetValues[_REG_CiCON // 4]
        word = (word & ~(1 << 5)) | ((iso_crc & 1) << 5)
        word = (word & ~(1 << 19)) | ((store_in_tef & 1) << 19)
        self._write_word(_REG_CiCON, word)

    def _tx_fifo_configure(
        self,
        channel,
        fifo_size=7,
        payload_size=CAN_PLSIZE_64,
        priority=1,
        rtr_enable=0,
        attempts=0,
    ):
        word = _canFifoResetValues[0]
        word |= 1 << 7
        word = (word & ~(1 << 6)) | ((rtr_enable & 1) << 6)
        word = (word & ~(0x1F << 16)) | ((priority & 0x1F) << 16)
        word = (word & ~(0x3 << 21)) | ((attempts & 0x3) << 21)
        word = (word & ~(0x1F << 24)) | ((fifo_size & 0x1F) << 24)
        word = (word & ~(0x7 << 29)) | ((payload_size & 0x7) << 29)
        self._write_word(_REG_CiFIFOCON + channel * _FIFO_OFFSET, word)

    def _rx_fifo_configure(
        self, channel, fifo_size=15, payload_size=CAN_PLSIZE_64, timestamp=0
    ):
        word = _canFifoResetValues[0]
        word &= ~(1 << 7)
        word = (word & ~(1 << 5)) | ((timestamp & 1) << 5)
        word = (word & ~(0x1F << 24)) | ((fifo_size & 0x1F) << 24)
        word = (word & ~(0x7 << 29)) | ((payload_size & 0x7) << 29)
        self._write_word(_REG_CiFIFOCON + channel * _FIFO_OFFSET, word)

    # -----------------------------------------------------------------------
    # Filter / mask
    # -----------------------------------------------------------------------

    def _filter_object_configure(self, filt, sid=0, eid=0, sid11=0, exide=0):
        word = (
            (sid & 0x7FF)
            | ((eid & 0x3FFFF) << 11)
            | ((sid11 & 1) << 29)
            | ((exide & 1) << 30)
        )
        self._write_word(_REG_CiFLTOBJ + filt * _FILTER_OFFSET, word)

    def _filter_mask_configure(self, filt, msid=0, meid=0, msid11=0, mide=0):
        word = (
            (msid & 0x7FF)
            | ((meid & 0x3FFFF) << 11)
            | ((msid11 & 1) << 29)
            | ((mide & 1) << 30)
        )
        self._write_word(_REG_CiMASK + filt * _FILTER_OFFSET, word)

    def _filter_to_fifo_link(self, filt, channel, enable=True):
        self._write_byte(
            _REG_CiFLTCON + filt, (channel & 0x1F) | (0x80 if enable else 0x00)
        )

    def _filter_disable(self, filt):
        a = _REG_CiFLTCON + filt
        self._write_byte(a, self._read_byte(a) & ~0x80)

    # -----------------------------------------------------------------------
    # Bit time calculation
    # -----------------------------------------------------------------------

    def _calc_bittime(self, arb_bitrate, tol_ppm=10000):
        MAX_BRP = 256
        MAX_ARB_PS1 = 256
        MAX_ARB_PS2 = 128
        MAX_DATA_PS1 = 32
        MAX_DATA_PS2 = 16

        if self._data_factor <= 1:
            max_tq = MAX_ARB_PS1 + MAX_ARB_PS2 + 1
            brp = MAX_BRP
            smallest_err = 0xFFFFFFFF
            best_brp = 1
            best_tq = 4
            tq = self._sys_clock // arb_bitrate // brp

            while tq <= max_tq + 1 and brp > 0:
                if 4 <= tq <= max_tq:
                    err = self._sys_clock - arb_bitrate * tq * brp
                    if err <= smallest_err:
                        smallest_err = err
                        best_brp = brp
                        best_tq = tq
                if 3 <= tq < max_tq:
                    err = arb_bitrate * (tq + 1) * brp - self._sys_clock
                    if err <= smallest_err:
                        smallest_err = err
                        best_brp = brp
                        best_tq = tq + 1
                brp -= 1
                tq = (self._sys_clock // arb_bitrate // brp) if brp else max_tq + 1

            ps2 = best_tq // 5
            if ps2 == 0:
                ps2 = 1
            elif ps2 > MAX_ARB_PS2:
                ps2 = MAX_ARB_PS2
            ps1 = best_tq - ps2 - 1
            if ps1 > MAX_ARB_PS1:
                ps2 += ps1 - MAX_ARB_PS1
                ps1 = MAX_ARB_PS1

            self._brp = best_brp
            self._arb_ps1 = ps1
            self._arb_ps2 = ps2
            self._arb_sjw = ps2
            self._data_ps1 = ps1
            self._data_ps2 = ps2
            self._data_sjw = ps2

        else:
            data_bitrate = arb_bitrate * self._data_factor
            max_data_tq = MAX_DATA_PS1 + MAX_DATA_PS2
            smallest_err = 0xFFFFFFFF
            best_brp = MAX_BRP
            best_data_tq = max_data_tq
            data_tq = 4
            brp = self._sys_clock // data_bitrate // data_tq

            while data_tq <= max_data_tq and brp > 0:
                if brp <= MAX_BRP:
                    err = self._sys_clock - data_bitrate * data_tq * brp
                    if err <= smallest_err:
                        smallest_err = err
                        best_brp = brp
                        best_data_tq = data_tq
                if brp < MAX_BRP:
                    err = data_bitrate * data_tq * (brp + 1) - self._sys_clock
                    if err <= smallest_err:
                        smallest_err = err
                        best_brp = brp + 1
                        best_data_tq = data_tq
                data_tq += 1
                brp = (self._sys_clock // data_bitrate // data_tq) if data_tq else 0

            data_ps2 = best_data_tq // 5
            if data_ps2 == 0:
                data_ps2 = 1
            data_ps1 = best_data_tq - data_ps2 - 1
            if data_ps1 > MAX_DATA_PS1:
                data_ps2 += data_ps1 - MAX_DATA_PS1
                data_ps1 = MAX_DATA_PS1

            tdco = best_brp * data_ps1
            self._tdco = min(tdco, 63)
            self._data_ps1 = data_ps1
            self._data_ps2 = data_ps2
            self._data_sjw = data_ps2

            arb_tq = best_data_tq * self._data_factor
            arb_ps2 = arb_tq // 5
            if arb_ps2 == 0:
                arb_ps2 = 1
            arb_ps1 = arb_tq - arb_ps2 - 1
            if arb_ps1 > MAX_ARB_PS1:
                arb_ps2 += arb_ps1 - MAX_ARB_PS1
                arb_ps1 = MAX_ARB_PS1

            self._brp = best_brp
            self._arb_ps1 = arb_ps1
            self._arb_ps2 = arb_ps2
            self._arb_sjw = arb_ps2

    def _bittime_configure_nominal(self):
        word = (
            ((self._arb_sjw - 1) & 0x7F)
            | (((self._arb_ps2 - 1) & 0x7F) << 8)
            | (((self._arb_ps1 - 1) & 0xFF) << 16)
            | (((self._brp - 1) & 0xFF) << 24)
        )
        self._write_word(_REG_CiNBTCFG, word)

    def _bittime_configure_data(self, ssp_mode=CAN_SSP_MODE_AUTO):
        word = (
            ((self._data_sjw - 1) & 0xF)
            | (((self._data_ps2 - 1) & 0xF) << 8)
            | (((self._data_ps1 - 1) & 0x1F) << 16)
            | (((self._brp - 1) & 0xFF) << 24)
        )
        self._write_word(_REG_CiDBTCFG, word)

        tdc = _canControlResetValues[_REG_CiTDC // 4]
        tdc = (tdc & ~(0x3 << 16)) | ((ssp_mode & 0x3) << 16)
        tdc = (tdc & ~(0x7F << 8)) | ((self._tdco & 0x7F) << 8)
        self._write_word(_REG_CiTDC, tdc)

    def _bittime_configure(self, speedset, ssp_mode, clk):
        self._data_factor = (speedset >> 24) & 0xFF
        arb_bitrate = speedset & 0xFFFFF
        if clk == MCP2518FD_10MHz:
            self._sys_clock = 10_000_000
        elif clk == MCP2518FD_20MHz:
            self._sys_clock = 20_000_000
        else:
            self._sys_clock = 40_000_000
        self._calc_bittime(arb_bitrate)
        self._bittime_configure_nominal()
        self._bittime_configure_data(ssp_mode)

    # -----------------------------------------------------------------------
    # Operation mode
    # -----------------------------------------------------------------------

    def _op_mode_select(self, mode):
        d = self._read_byte(_REG_CiCON + 3)
        self._write_byte(_REG_CiCON + 3, (d & ~0x07) | (mode & 0x07))

    def _op_mode_get(self):
        return (self._read_byte(_REG_CiCON + 2) >> 5) & 0x7

    # -----------------------------------------------------------------------
    # GPIO
    # -----------------------------------------------------------------------

    def _gpio_mode_configure(self, gpio0=GPIO_MODE_INT, gpio1=GPIO_MODE_INT):
        a = _REG_IOCON + 3
        d = self._read_byte(a)
        d = (d & ~0x01) | (gpio0 & 0x01)
        d = (d & ~0x02) | ((gpio1 & 0x01) << 1)
        self._write_byte(a, d)

    # -----------------------------------------------------------------------
    # Events / interrupts
    # -----------------------------------------------------------------------

    def _tx_channel_event_enable(self, channel, flags):
        a = _REG_CiFIFOCON + channel * _FIFO_OFFSET
        self._write_byte(a, self._read_byte(a) | (flags & CAN_TX_FIFO_ALL_EVENTS))

    def _rx_channel_event_enable(self, channel, flags):
        if channel == CAN_TXQUEUE_CH0:
            return
        a = _REG_CiFIFOCON + channel * _FIFO_OFFSET
        self._write_byte(a, self._read_byte(a) | (flags & CAN_RX_FIFO_ALL_EVENTS))

    def _module_event_enable(self, flags):
        w = self._read_half_word(_REG_CiINTENABLE)
        self._write_half_word(_REG_CiINTENABLE, w | (flags & CAN_ALL_EVENTS))

    # -----------------------------------------------------------------------
    # TX channel status / load / update
    # -----------------------------------------------------------------------

    def _tx_channel_event_get(self, channel):
        a = _REG_CiFIFOSTA + channel * _FIFO_OFFSET
        return self._read_byte(a) & CAN_TX_FIFO_ALL_EVENTS

    def _tx_channel_event_attempt_clear(self, channel):
        a = _REG_CiFIFOSTA + channel * _FIFO_OFFSET
        self._write_byte(a, self._read_byte(a) & ~CAN_TX_FIFO_ATTEMPTS_EXHAUSTED_EVENT)

    def _tx_channel_update(self, channel, flush):
        # Write to byte 1 of CiFIFOCON (bits 8-15):
        #   bit 0 of byte = UINC (bit 8 of word)
        #   bit 1 of byte = TxRequest (bit 9 of word)
        a = _REG_CiFIFOCON + channel * _FIFO_OFFSET + 1
        self._write_byte(a, 0x03 if flush else 0x01)

    def _tx_channel_load(self, channel, id_word, ctrl_word, data, flush):
        fifo_regs = self._read_word_array(_REG_CiFIFOCON + channel * _FIFO_OFFSET, 3)

        if not (fifo_regs[0] & (1 << 7)):
            return -2

        if dlc2len(ctrl_word & 0xF) < len(data):
            return -3

        ua = fifo_regs[2] & 0xFFF
        a = ua + _RAM_START

        buf = bytearray(8 + len(data))
        buf[0] = id_word & 0xFF
        buf[1] = (id_word >> 8) & 0xFF
        buf[2] = (id_word >> 16) & 0xFF
        buf[3] = (id_word >> 24) & 0xFF
        buf[4] = ctrl_word & 0xFF
        buf[5] = (ctrl_word >> 8) & 0xFF
        buf[6] = (ctrl_word >> 16) & 0xFF
        buf[7] = (ctrl_word >> 24) & 0xFF
        buf[8:] = data

        pad = (4 - len(buf) % 4) % 4
        if pad:
            buf += bytes(pad)

        self._write_byte_array(a, buf)
        self._tx_channel_update(channel, flush)
        return 0

    def _tx_message_queue(self, id_word, ctrl_word, data):
        for _ in range(_MAX_TXQUEUE_ATTEMPTS):
            if self._tx_channel_event_get(_APP_TX_FIFO) & CAN_TX_FIFO_NOT_FULL_EVENT:
                return self._tx_channel_load(
                    _APP_TX_FIFO, id_word, ctrl_word, data, True
                )
        return -2

    # -----------------------------------------------------------------------
    # RX channel status / receive
    # -----------------------------------------------------------------------

    def _rx_channel_event_get(self, channel):
        if channel == CAN_TXQUEUE_CH0:
            return 0
        a = _REG_CiFIFOSTA + channel * _FIFO_OFFSET
        return self._read_byte(a) & CAN_RX_FIFO_ALL_EVENTS

    def _rx_channel_status_get(self, channel):
        a = _REG_CiFIFOSTA + channel * _FIFO_OFFSET
        return self._read_byte(a) & 0x0F

    def _rx_channel_update(self, channel):
        a = _REG_CiFIFOCON + channel * _FIFO_OFFSET + 1
        self._write_byte(a, 0x01)  # UINC

    def _rx_message_get(self, channel, max_bytes=64):
        fifo_regs = self._read_word_array(_REG_CiFIFOCON + channel * _FIFO_OFFSET, 3)
        timestamp_en = bool(fifo_regs[0] & (1 << 5))

        ua = fifo_regs[2] & 0xFFF
        a = ua + _RAM_START

        n = max_bytes + 8 + (4 if timestamp_en else 0)
        pad = (4 - n % 4) % 4
        n = min(n + pad, 76)

        ba = self._read_byte_array(a, n)

        id_word = ba[0] | (ba[1] << 8) | (ba[2] << 16) | (ba[3] << 24)
        ctrl_word = ba[4] | (ba[5] << 8) | (ba[6] << 16) | (ba[7] << 24)

        ide = bool(ctrl_word & (1 << 4))
        rtr = bool(ctrl_word & (1 << 5))
        dlc = ctrl_word & 0xF

        sid = id_word & 0x7FF
        eid = (id_word >> 11) & 0x3FFFF
        can_id = (eid | (sid << 18)) if ide else sid

        data_off = 12 if timestamp_en else 8
        n_data = dlc2len(dlc)
        data = bytes(ba[data_off : data_off + n_data])

        self._rx_channel_update(channel)
        return can_id, int(ide), int(rtr), dlc, data

    # -----------------------------------------------------------------------
    # Error state
    # -----------------------------------------------------------------------

    def _error_state_get(self):
        return self._read_byte(_REG_CiTREC + 2) & CAN_ERROR_ALL

    def _error_count_state_get(self):
        w = self._read_word(_REG_CiTREC)
        return (w >> 8) & 0xFF, w & 0xFF, (w >> 16) & CAN_ERROR_ALL

    # -----------------------------------------------------------------------
    # Low-power mode
    # -----------------------------------------------------------------------

    def _lpm_enable(self):
        self._write_byte(_REG_OSC, self._read_byte(_REG_OSC) | 0x08)

    def _lpm_disable(self):
        self._write_byte(_REG_OSC, self._read_byte(_REG_OSC) & ~0x08)

    # -----------------------------------------------------------------------
    # Internal init sequence
    # -----------------------------------------------------------------------

    @staticmethod
    def _compat_speed(speedset):
        if speedset > 0x100:
            return speedset
        _map = {
            CAN_5KBPS: BITRATE(5000, 0),
            CAN_10KBPS: BITRATE(10000, 0),
            CAN_20KBPS: BITRATE(20000, 0),
            CAN_25KBPS: BITRATE(25000, 0),
            CAN_31K25BPS: BITRATE(31250, 0),
            CAN_33KBPS: BITRATE(33000, 0),
            CAN_40KBPS: BITRATE(40000, 0),
            CAN_50KBPS: BITRATE(50000, 0),
            CAN_80KBPS: BITRATE(80000, 0),
            CAN_83K3BPS: BITRATE(83300, 0),
            CAN_95KBPS: BITRATE(95000, 0),
            CAN_100KBPS: BITRATE(100000, 0),
            CAN_125KBPS: BITRATE(125000, 0),
            CAN_200KBPS: BITRATE(200000, 0),
            CAN_250KBPS: BITRATE(250000, 0),
            CAN_500KBPS: BITRATE(500000, 0),
            CAN_666KBPS: BITRATE(666000, 0),
            CAN_800KBPS: BITRATE(800000, 0),
            CAN_1000KBPS: BITRATE(1000000, 0),
        }
        return _map.get(speedset, BITRATE(500000, 0))

    def _init(self, speedset, clock):
        self._reset()
        self._ecc_enable()
        self._ram_init(0xFF)
        self._configure(iso_crc=1, store_in_tef=0)

        self._tx_fifo_configure(
            _APP_TX_FIFO, fifo_size=7, payload_size=CAN_PLSIZE_64, priority=1
        )
        self._rx_fifo_configure(_APP_RX_FIFO, fifo_size=15, payload_size=CAN_PLSIZE_64)

        self._filter_object_configure(CAN_FILTER0)
        self._filter_mask_configure(CAN_FILTER0)
        self._filter_to_fifo_link(CAN_FILTER0, _APP_RX_FIFO, True)

        self._bittime_configure(speedset, CAN_SSP_MODE_AUTO, clock)

        self._gpio_mode_configure(GPIO_MODE_INT, GPIO_MODE_INT)
        self._rx_channel_event_enable(_APP_RX_FIFO, CAN_RX_FIFO_NOT_EMPTY_EVENT)
        self._module_event_enable(CAN_TX_EVENT | CAN_RX_EVENT)

        self._op_mode_select(self._mode)
        time.sleep_ms(5)

        original = self._read_byte(_REG_ECCCON)
        test_val = original ^ 0x01
        self._write_byte(_REG_ECCCON, test_val)
        time.sleep_ms(2)
        readback = self._read_byte(_REG_ECCCON)
        self._write_byte(_REG_ECCCON, original)

        if readback != test_val:
            return CAN_FAILINIT
        return CAN_OK

    # -----------------------------------------------------------------------
    # Internal send helper
    # -----------------------------------------------------------------------

    def _send_msg(self, data, can_id, ext, rtr):
        n = len(data)
        dlc = len2dlc(n)

        if ext:
            id_word = ((can_id >> 18) & 0x7FF) | ((can_id & 0x3FFFF) << 11)
        else:
            id_word = can_id & 0x7FF

        ctrl_word = dlc & 0xF
        if ext:
            ctrl_word |= 1 << 4
        if rtr:
            ctrl_word |= 1 << 5
        ctrl_word |= 1 << 6  # BRS
        if n > 8:
            ctrl_word |= 1 << 7  # FDF

        err = self._tx_message_queue(id_word, ctrl_word, bytes(data[:n]))
        if err < 0:
            if err == -2:
                return CAN_SENDMSGTIMEOUT
            if err == -3:
                return CAN_FAILTX
            return CAN_FAILINIT
        return CAN_OK

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def begin(self, speedset, clockset=MCP2518FD_20MHz):
        """Initialize the CAN controller.

        :param speedset: Baud rate — use CAN_125KBPS etc., or BITRATE(arb, factor) for CAN FD
        :param clockset: Oscillator frequency — MCP2518FD_40MHz / _20MHz / _10MHz
        :returns: CAN_OK on success, CAN_FAILINIT on failure
        """
        speedset = self._compat_speed(speedset)
        return self._init(speedset, clockset)

    def sendMsgBuf(self, can_id, ext, rtr_or_len, len_or_buf, buf=None, wait_sent=True):
        """Send a CAN message.

        4-arg form: sendMsgBuf(id, ext, length, data)       — rtr=0
        5-arg form: sendMsgBuf(id, ext, rtr, length, data)
        """
        if buf is None:
            length = rtr_or_len
            data = len_or_buf
            rtr = 0
        else:
            rtr = rtr_or_len
            length = len_or_buf
            data = buf
        return self._send_msg(data[:length], can_id, int(ext), int(rtr))

    def trySendMsgBuf(self, can_id, ext, rtr, length, data, itx_buf=0xFF):
        """Send without waiting. Returns CAN_OK or error code."""
        return self._send_msg(data[:length], can_id, int(ext), int(rtr))

    def checkReceive(self):
        """Returns CAN_MSGAVAIL if message waiting, CAN_NOMSG otherwise."""
        status = self._rx_channel_status_get(_APP_RX_FIFO)
        return CAN_MSGAVAIL if (status & CAN_RX_FIFO_NOT_EMPTY) else CAN_NOMSG

    def readMsgBuf(self, buf=None):
        """Read received message. Updates can_id, ext_flg, rtr.

        :param buf: optional bytearray to fill (ignored; returned as bytes)
        :returns: (length, data_bytes)
        """
        self.can_id, self.ext_flg, self.rtr, dlc, data = self._rx_message_get(
            _APP_RX_FIFO, 64
        )
        return len(data), data

    def readMsgBufID(self, buf=None):
        """Read received message with ID.

        :returns: (can_id, length, data_bytes)
        """
        length, data = self.readMsgBuf()
        return self.can_id, length, data

    def getCanId(self):
        """Return CAN ID of last received message."""
        return self.can_id

    def isRemoteRequest(self):
        """Return 1 if last received message was RTR."""
        return self.rtr

    def isExtendedFrame(self):
        """Return 1 if last received message had extended ID."""
        return self.ext_flg

    def checkError(self):
        """Return current error state flags."""
        return self._error_state_get()

    def readRxTxStatus(self):
        """Return RX FIFO event flags."""
        return self._rx_channel_event_get(_APP_RX_FIFO)

    def clearBufferTransmitIfFlags(self, flags=0):
        """Clear TX attempt exhausted flag."""
        self._tx_channel_event_attempt_clear(_APP_TX_FIFO)

    def enableTxInterrupt(self, enable=True):
        """Enable or disable TX interrupt."""
        if enable:
            self._module_event_enable(CAN_TX_EVENT)

    def init_Mask(self, num, ext, ul_data):
        """Configure acceptance mask for filter num.

        :param num:     Filter number (0-31)
        :param ext:     1 = extended ID mask, 0 = standard ID mask
        :param ul_data: Mask bits
        """
        self._op_mode_select(CAN_CONFIGURATION_MODE)
        self._filter_mask_configure(num, msid=ul_data, mide=ext)
        self._op_mode_select(self._mode)

    def init_Filt(self, num, ext, ul_data):
        """Configure acceptance filter for filter num.

        :param num:     Filter number (0-31)
        :param ext:     1 = extended ID, 0 = standard ID
        :param ul_data: Filter ID bits
        """
        self._op_mode_select(CAN_CONFIGURATION_MODE)
        if ext:
            self._filter_object_configure(num, eid=ul_data, exide=1)
        else:
            self._filter_object_configure(num, sid=ul_data, exide=0)
        self._op_mode_select(self._mode)

    def init_Filt_Mask(self, num, ext, f, m):
        """Configure filter and mask together and link to RX FIFO.

        :param num: Filter number
        :param ext: Extended ID flag (used as MEID value)
        :param f:   Filter SID value
        :param m:   Mask MSID value
        """
        self._filter_disable(num)
        self._filter_object_configure(num, sid=f, eid=ext)
        self._filter_mask_configure(num, msid=m, meid=ext, mide=1)
        self._filter_to_fifo_link(num, _APP_RX_FIFO, True)

    def setSleepWakeup(self, enable):
        """Enable or disable low-power wake-up mode."""
        if enable:
            self._lpm_enable()
        else:
            self._lpm_disable()

    def sleep(self):
        """Put device into sleep mode."""
        if self.getMode() != CAN_SLEEP_MODE:
            self._op_mode_select(CAN_SLEEP_MODE)
        return CAN_OK

    def wake(self):
        """Wake device from sleep, restoring previous mode."""
        if self.getMode() != self._mode:
            self._op_mode_select(self._mode)
        return CAN_OK

    def getMode(self):
        """Return current operation mode."""
        return self._op_mode_get()

    def setMode(self, op_mode):
        """Set operation mode without persisting (use __setMode to persist)."""
        if op_mode != CAN_SLEEP_MODE:
            self._mode = op_mode
        return CAN_OK

    def __setMode(self, op_mode):
        """Set and persist operation mode."""
        if op_mode != CAN_SLEEP_MODE:
            self._mode = op_mode
        return self._op_mode_select(self._mode)

    def mcpPinMode(self, pin, mode):
        """Configure MCP GPIO pin as interrupt output or GPIO."""
        a = _REG_IOCON + 3
        d = self._read_byte(a)
        if pin == GPIO_PIN_0:
            d = (d & ~0x01) | (mode & 0x01)
        elif pin == GPIO_PIN_1:
            d = (d & ~0x02) | ((mode & 0x01) << 1)
        self._write_byte(a, d)

    def mcpDigitalWrite(self, pin, state):
        """Write HIGH or LOW to MCP GPIO output pin."""
        a = _REG_IOCON + 1
        d = self._read_byte(a)
        if pin == GPIO_PIN_0:
            d = (d & ~0x01) | (state & 0x01)
        elif pin == GPIO_PIN_1:
            d = (d & ~0x02) | ((state & 0x01) << 1)
        self._write_byte(a, d)

    def mcpDigitalRead(self, pin):
        """Read state of MCP GPIO input pin."""
        d = self._read_byte(_REG_IOCON + 2)
        if pin == GPIO_PIN_0:
            return d & 0x01
        if pin == GPIO_PIN_1:
            return (d >> 1) & 0x01
        return -1
