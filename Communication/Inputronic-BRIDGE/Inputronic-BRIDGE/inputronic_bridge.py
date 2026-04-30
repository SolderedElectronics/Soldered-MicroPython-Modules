# FILE: inputronic_bridge.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython driver for the Soldered Inputronic BRIDGE
#        Supports UART, I2C, and SPI transports.
#        Parses keyboard, mouse, MIDI, descriptor, and raw HID events.
# WORKS WITH: Inputronic BRIDGE: www.soldered.com
# LAST UPDATED: 2026-04-30

import time
from machine import I2C, SPI, UART, Pin

# Protocol constants
PROTOCOL_UART = 0
PROTOCOL_I2C = 1
PROTOCOL_SPI = 2

_SPI_MAX_LEN = 64
_I2C_MAX_LEN = 48
_UART_BUF_MAX = 512
_SPI_BUF_MAX = 256


class KeyboardEvent:
    def __init__(self):
        self.payload = ""
        self.key = 0
        self.keys = [""] * 8
        self.keyCount = 0
        self.valid = False


class MouseEvent:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.scroll = 0
        self.btnLeft = False
        self.btnRight = False
        self.btnMiddle = False
        self.btnBackward = False
        self.btnForward = False
        self.btnScrollWheel = False
        self.valid = False


class MIDIEvent:
    def __init__(self):
        self.b1 = 0
        self.b2 = 0
        self.b3 = 0
        self.valid = False


class DescriptorEvent:
    def __init__(self):
        self.hex = ""
        self.valid = False


class HidRawEvent:
    def __init__(self):
        self.hex = ""
        self.valid = False


class EventBundle:
    def __init__(self):
        self.keyboard = KeyboardEvent()
        self.mouse = MouseEvent()
        self.midi = MIDIEvent()
        self.descriptor = DescriptorEvent()
        self.hidRaw = HidRawEvent()


class InputronicBridge:
    """
    MicroPython driver for the Soldered Inputronic BRIDGE.

    Supports UART, I2C, and SPI transports.

    Usage (I2C example):
        from machine import I2C, Pin
        from inputronic_bridge import InputronicBridge, PROTOCOL_I2C

        i2c = I2C(0, scl=Pin(22), sda=Pin(21))
        bridge = InputronicBridge(PROTOCOL_I2C, i2c=i2c)
        while True:
            events = bridge.pollEvents()
            if events.keyboard.valid:
                print(events.keyboard.payload)
    """

    def __init__(
        self,
        protocol,
        i2c=None,
        i2cAddr=0x50,
        uart=None,
        spi=None,
        spiCs=None,
        spiHz=1000000,
        interruptPin=None,
        activeHigh=True,
        interruptCallback=None,
    ):
        """
        Initialize the Inputronic BRIDGE.

        :param protocol:           PROTOCOL_UART, PROTOCOL_I2C, or PROTOCOL_SPI
        :param i2c:                Initialized I2C object (PROTOCOL_I2C)
        :param i2cAddr:            I2C slave address (default 0x50)
        :param uart:               Initialized UART object (PROTOCOL_UART)
        :param spi:                Initialized SPI object (PROTOCOL_SPI)
        :param spiCs:              Pin object for SPI chip-select (PROTOCOL_SPI)
        :param spiHz:              SPI clock frequency in Hz (default 1 MHz)
        :param interruptPin:       Pin object for interrupt input (optional)
        :param activeHigh:         True = interrupt on rising edge, False = falling
        :param interruptCallback:  Callable invoked from IRQ context on data ready
        """
        self._protocol = protocol
        self._i2c = i2c
        self._i2cAddr = i2cAddr
        self._uart = uart
        self._spi = spi
        self._spiCs = spiCs
        self._spiHz = spiHz

        self._interruptPin = interruptPin
        self._activeHigh = activeHigh
        self._interruptFlag = False
        self._interruptEnabled = interruptPin is not None
        self._userCallback = interruptCallback

        self._latest = EventBundle()

        self._requestDescPending = False
        self._requestHidRawPending = False
        self._pollHidRawEnabled = False
        self._expectingHidRawOnly = False

        self._uartBuffer = ""
        self._spiBuffer = ""
        self._spiFrameStartMs = 0
        self._spiPendingAck = False
        self._spiPendingCommand = ""

        if self._interruptEnabled:
            self._configureInterrupt(interruptPin, activeHigh)

        if not self._checkConnection():
            raise Exception("Inputronic BRIDGE not found — check wiring and protocol")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def configureI2cAddress(self, addr):
        """Change the I2C slave address."""
        self._i2cAddr = addr

    def requestDescriptor(self):
        """Request the USB descriptor on the next poll."""
        self._requestDescPending = True

    def requestHidRawOnce(self):
        """Request one raw HID report on the next poll."""
        self._requestHidRawPending = True
        self._expectingHidRawOnly = True

    def setHidRawPolling(self, enabled):
        """Enable or disable continuous raw HID polling."""
        self._pollHidRawEnabled = enabled
        self._expectingHidRawOnly = False

    def setInterruptMode(self, enable, pin=None, activeHigh=True):
        """Enable or disable interrupt-driven polling."""
        self._interruptEnabled = enable
        if enable and pin is not None:
            self._interruptPin = pin
            self._configureInterrupt(pin, activeHigh)
        elif not enable and self._interruptPin is not None:
            self._interruptPin.irq(handler=None)

    def onDataReady(self, callback):
        """Register a callback invoked from IRQ context when the BRIDGE signals data."""
        self._userCallback = callback

    def feedLine(self, line):
        """Feed a raw framed line directly into the parser."""
        self._parseMessage(line)

    def pollEvents(self):
        """
        Poll the transport for new events.

        Returns an EventBundle. Check the .valid field on each sub-event before use.
        In interrupt mode the method returns immediately with no bus traffic unless
        the interrupt flag is set.
        """
        if self._protocol == PROTOCOL_UART:
            self._pollUart()
        elif self._protocol == PROTOCOL_I2C:
            self._pollI2c()
        elif self._protocol == PROTOCOL_SPI:
            self._pollSpiTransport()

        out = self._latest
        self._latest = EventBundle()
        return out

    # ------------------------------------------------------------------
    # Connection check
    # ------------------------------------------------------------------

    def _checkConnection(self):
        if self._protocol == PROTOCOL_I2C:
            return self._pingI2c()
        elif self._protocol == PROTOCOL_SPI:
            return self._pingSpi()
        elif self._protocol == PROTOCOL_UART:
            return self._pingUart()
        return False

    def _pingI2c(self):
        if self._i2c is None:
            return False
        for _ in range(10):
            try:
                self._i2c.writeto(self._i2cAddr, b"PING")
            except OSError:
                time.sleep_ms(50)
                continue
            for _ in range(10):
                time.sleep_ms(5)
                try:
                    raw = self._i2c.readfrom(self._i2cAddr, _I2C_MAX_LEN)
                except OSError:
                    continue
                if len(raw) > 1:
                    payloadLen = raw[0]
                    if 0 < payloadLen < _I2C_MAX_LEN and payloadLen <= len(raw) - 1:
                        msg = bytes(raw[1 : payloadLen + 1]).decode("utf-8", "ignore").strip()
                        if msg == "TS;PONG;TE":
                            try:
                                self._i2c.writeto(self._i2cAddr, b"ACK")
                            except OSError:
                                pass
                            return True
        return False

    def _pingSpi(self):
        if self._spi is None or self._spiCs is None:
            return False
        tx = bytearray(_SPI_MAX_LEN)
        rx = bytearray(_SPI_MAX_LEN)
        tx[0:4] = b"PING"
        self._spiCs(0)
        self._spi.write_readinto(tx, rx)
        self._spiCs(1)
        time.sleep_ms(50)
        tx = bytearray(_SPI_MAX_LEN)
        rx = bytearray(_SPI_MAX_LEN)
        self._spiCs(0)
        self._spi.write_readinto(tx, rx)
        self._spiCs(1)
        payloadLen = rx[0]
        if 0 < payloadLen < _SPI_MAX_LEN:
            msg = bytes(rx[1 : payloadLen + 1]).decode("utf-8", "ignore")
            if msg == "TS;PONG;TE":
                tx = bytearray(_SPI_MAX_LEN)
                tx[0:3] = b"ACK"
                rx = bytearray(_SPI_MAX_LEN)
                self._spiCs(0)
                self._spi.write_readinto(tx, rx)
                self._spiCs(1)
                return True
        return False

    def _pingUart(self):
        if self._uart is None:
            return False
        self._uart.write(b"PING\n")
        deadline = time.ticks_add(time.ticks_ms(), 500)
        buf = ""
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            while self._uart.any():
                b = self._uart.read(1)
                if b:
                    buf += b.decode("utf-8", "ignore")
            if "TS;PONG;TE" in buf:
                return True
            time.sleep_ms(10)
        return False

    # ------------------------------------------------------------------
    # Interrupt
    # ------------------------------------------------------------------

    def _configureInterrupt(self, pin, activeHigh):
        trigger = Pin.IRQ_RISING if activeHigh else Pin.IRQ_FALLING
        pin.irq(trigger=trigger, handler=self._isrHandler)

    def _isrHandler(self, pin):
        self._interruptFlag = True
        if self._userCallback is not None:
            self._userCallback()

    # ------------------------------------------------------------------
    # Transport pollers
    # ------------------------------------------------------------------

    def _pollUart(self):
        if self._uart is None:
            return

        flag = self._interruptFlag
        if flag:
            self._interruptFlag = False

        if self._interruptEnabled and not flag:
            return

        while self._uart.any():
            b = self._uart.read(1)
            if b:
                self._uartBuffer += b.decode("utf-8", "ignore")

        if len(self._uartBuffer) > _UART_BUF_MAX:
            idx = self._uartBuffer.rfind("TS;")
            if idx >= 0:
                self._uartBuffer = self._uartBuffer[idx:]
            else:
                self._uartBuffer = ""

        while True:
            tePos = self._uartBuffer.find(";TE")
            if tePos == -1:
                break
            fullMsg = self._uartBuffer[: tePos + 3]
            self.feedLine(fullMsg)
            self._uartBuffer = self._uartBuffer[tePos + 3:].lstrip()

    def _pollI2c(self):
        if self._i2c is None:
            return

        flag = self._interruptFlag
        if flag:
            self._interruptFlag = False

        if self._interruptEnabled and not flag and not self._requestDescPending and not self._requestHidRawPending:
            return

        if not self._interruptEnabled:
            if self._requestDescPending:
                self._sendI2cCommand(b"REQ:DESC")
                self._requestDescPending = False
            if self._requestHidRawPending or self._pollHidRawEnabled:
                self._sendI2cCommand(b"REQ:HIDRAW")
                self._requestHidRawPending = False

        try:
            raw = self._i2c.readfrom(self._i2cAddr, _I2C_MAX_LEN)
        except OSError:
            return

        shouldAck = False
        if len(raw) > 1:
            payloadLen = raw[0]
            if payloadLen > 0:
                shouldAck = True
            if 0 < payloadLen < _I2C_MAX_LEN and payloadLen <= len(raw) - 1:
                msg = bytes(raw[1 : payloadLen + 1]).decode("utf-8", "ignore").strip()
                if msg.startswith("TS;") and msg.endswith(";TE"):
                    self.feedLine(msg)

        if shouldAck:
            self._sendI2cCommand(b"ACK")

    def _pollSpiTransport(self):
        if self._spi is None or self._spiCs is None:
            return

        flag = self._interruptFlag
        if flag:
            self._interruptFlag = False

        if self._interruptEnabled and not flag and not self._requestDescPending and not self._requestHidRawPending:
            return

        if self._interruptEnabled and flag:
            time.sleep_us(50)

        if not self._interruptEnabled:
            if self._requestDescPending:
                self._spiPendingCommand = "REQ:DESC"
                self._requestDescPending = False
            if self._requestHidRawPending or self._pollHidRawEnabled:
                self._spiPendingCommand = "REQ:HIDRAW"
                self._requestHidRawPending = False

        self._doSpiPoll()

    def _doSpiPoll(self):
        tx = bytearray(_SPI_MAX_LEN)
        rx = bytearray(_SPI_MAX_LEN)

        if self._spiPendingAck:
            tx[0:3] = b"ACK"
            self._spiPendingAck = False
        elif self._spiPendingCommand:
            cmd = self._spiPendingCommand.encode()
            tx[: len(cmd)] = cmd
            self._spiPendingCommand = ""

        self._spiCs(0)
        self._spi.write_readinto(tx, rx)
        self._spiCs(1)

        payloadLen = rx[0]
        if 0 < payloadLen < _SPI_MAX_LEN:
            chunk = bytes(rx[1 : payloadLen + 1]).decode("utf-8", "ignore")
            self._spiPendingAck = True
            self._spiBuffer += chunk

            if len(self._spiBuffer) > _SPI_BUF_MAX:
                idx = self._spiBuffer.rfind("TS;")
                if idx >= 0:
                    self._spiBuffer = self._spiBuffer[idx:]
                else:
                    self._spiBuffer = ""

            while True:
                tsPos = self._spiBuffer.find("TS;")
                if tsPos < 0:
                    self._spiBuffer = ""
                    self._spiFrameStartMs = 0
                    break
                if tsPos > 0:
                    self._spiBuffer = self._spiBuffer[tsPos:]
                if self._spiFrameStartMs == 0:
                    self._spiFrameStartMs = time.ticks_ms()
                tePos = self._spiBuffer.find(";TE")
                if tePos < 0:
                    if self._spiFrameStartMs and time.ticks_diff(time.ticks_ms(), self._spiFrameStartMs) > 30:
                        self._spiBuffer = self._spiBuffer[3:]
                        self._spiFrameStartMs = 0
                        continue
                    break
                fullMsg = self._spiBuffer[: tePos + 3]
                self.feedLine(fullMsg)
                self._spiBuffer = self._spiBuffer[tePos + 3:]
                self._spiFrameStartMs = 0

    # ------------------------------------------------------------------
    # I2C command helper
    # ------------------------------------------------------------------

    def _sendI2cCommand(self, cmd):
        try:
            self._i2c.writeto(self._i2cAddr, cmd)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Message parser
    # ------------------------------------------------------------------

    def _parseMessage(self, msgIn):
        msg = msgIn.strip()
        if "TS;MIDI;" in msg:
            self._parseMidi(msg)
        elif not self._expectingHidRawOnly and msg.startswith("TS;M;"):
            self._parseMouse(msg)
        elif not self._expectingHidRawOnly and msg.startswith("TS;K;"):
            self._parseKeyboard(msg)
        elif "TS;DESC;" in msg:
            self._parseDescriptor(msg)
        elif "TS;HIDRAW;" in msg:
            self._parseHidRaw(msg)
            self._expectingHidRawOnly = False

    def _parseKeyboard(self, msg):
        kPos = msg.find(";K;")
        end = msg.find(";TE")
        if kPos == -1 or end == -1 or end <= kPos:
            return
        keyStr = msg[kPos + 3 : end].replace("\\;", ";")
        kb = self._latest.keyboard
        kb.payload = keyStr
        kb.keyCount = 0
        kb.keys = [""] * 8
        kb.key = keyStr[0] if len(keyStr) == 1 else 0

        i = 0
        while i < len(keyStr) and kb.keyCount < 8:
            if keyStr[i] == "<":
                close = keyStr.find(">", i + 1)
                if close > i:
                    kb.keys[kb.keyCount] = keyStr[i : close + 1]
                    kb.keyCount += 1
                    i = close + 1
                    continue
            kb.keys[kb.keyCount] = keyStr[i]
            kb.keyCount += 1
            i += 1

        if kb.keyCount == 0 and len(keyStr) == 1:
            kb.keys[0] = keyStr
            kb.keyCount = 1

        kb.valid = True

    def _parseMidi(self, msgIn):
        start = msgIn.find("TS;MIDI;")
        if start < 0:
            return
        payload = msgIn[start + 8:]
        tePos = payload.find(";TE")
        if tePos >= 0:
            payload = payload[:tePos]

        pipe = payload.find("|")
        first = payload[:pipe] if pipe >= 0 else payload

        parts = []
        for token in first.split(";"):
            if token:
                try:
                    parts.append(int(token, 16))
                except ValueError:
                    pass

        if len(parts) == 3:
            self._latest.midi.b1 = parts[0]
            self._latest.midi.b2 = parts[1]
            self._latest.midi.b3 = parts[2]
            self._latest.midi.valid = True

    def _parseMouse(self, msgIn):
        msg = msgIn.strip()
        mPos = msg.find(";M;")
        end = msg.find(";TE")
        if mPos == -1 or end == -1 or end <= mPos:
            return
        body = msg[mPos + 3 : end]

        vals = []
        val = 0
        neg = False
        inNum = False
        for ch in body:
            if ch == "-":
                neg = True
                val = 0
                inNum = True
            elif "0" <= ch <= "9":
                val = val * 10 + (ord(ch) - ord("0"))
                inNum = True
            elif ch == ";":
                if inNum:
                    vals.append(-val if neg else val)
                    val = 0
                    neg = False
                    inNum = False
        if inNum:
            vals.append(-val if neg else val)

        if len(vals) >= 9:
            m = self._latest.mouse
            m.x = vals[0]
            m.y = vals[1]
            m.scroll = vals[2]
            m.btnLeft = bool(vals[3])
            m.btnRight = bool(vals[4])
            m.btnMiddle = bool(vals[5])
            m.btnBackward = bool(vals[6])
            m.btnForward = bool(vals[7])
            m.btnScrollWheel = bool(vals[8])
            m.valid = True

    def _parseDescriptor(self, msg):
        dPos = msg.find(";DESC;")
        end = msg.find(";TE")
        if dPos == -1 or end == -1 or end <= dPos:
            return
        start = dPos + 6
        if end > start:
            self._latest.descriptor.hex = msg[start:end]
            self._latest.descriptor.valid = True

    def _parseHidRaw(self, msg):
        hPos = msg.find(";HIDRAW;")
        end = msg.find(";TE")
        if hPos == -1 or end == -1 or end <= hPos:
            return
        start = hPos + 8
        if end > start:
            hexStr = msg[start:end]
            if hexStr:
                self._latest.hidRaw.hex = hexStr
                self._latest.hidRaw.valid = True
