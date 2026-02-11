# FILE: inputronic_keyboard.py
# AUTHOR: Marko Toldi @ Soldered
# BRIEF: MicroPython driver for Soldered Inputronic Keyboard (TI TCA8418)
# LAST UPDATED: 2026-02-11

import time
from machine import I2C, Pin
from os import uname

from inputronic_keymap import INPUTRONIC_KEYMAP_UPPER, INPUTRONIC_KEYMAP_LOWER
from inputronic_shiftmap import inputronic_apply_shift


# Default I2C address
INPUTRONIC_KBD_DEFAULT_ADDR = 0x34

# TCA8418 registers (subset)
TCA8418_REG_INT_STAT = 0x02
TCA8418_REG_KEY_LCK_EC = 0x03
TCA8418_REG_KEY_EVENT_A = 0x04

TCA8418_REG_KP_GPIO_1 = 0x1D
TCA8418_REG_KP_GPIO_2 = 0x1E
TCA8418_REG_KP_GPIO_3 = 0x1F

TCA8418_REG_GPI_EM_1 = 0x20
TCA8418_REG_GPI_EM_2 = 0x21
TCA8418_REG_GPI_EM_3 = 0x22

TCA8418_REG_GPIO_DIR_1 = 0x23
TCA8418_REG_GPIO_DIR_2 = 0x24
TCA8418_REG_GPIO_DIR_3 = 0x25

TCA8418_REG_GPIO_INT_LVL_1 = 0x26
TCA8418_REG_GPIO_INT_LVL_2 = 0x27
TCA8418_REG_GPIO_INT_LVL_3 = 0x28

TCA8418_REG_DEBOUNCE_DIS_1 = 0x29
TCA8418_REG_DEBOUNCE_DIS_2 = 0x2A
TCA8418_REG_DEBOUNCE_DIS_3 = 0x2B

TCA8418_REG_GPIO_INT_EN_1 = 0x1A
TCA8418_REG_GPIO_INT_EN_2 = 0x1B
TCA8418_REG_GPIO_INT_EN_3 = 0x1C

TCA8418_REG_GPIO_INT_STAT_1 = 0x11
TCA8418_REG_GPIO_INT_STAT_2 = 0x12
TCA8418_REG_GPIO_INT_STAT_3 = 0x13

TCA8418_STAT_GPI_INT = 0x02
TCA8418_STAT_K_INT = 0x01


# Simple "enum" for keymaps
IKMAP_UPPER = 0
IKMAP_LOWER = 1

# Type events (string labels; MicroPython-friendly)
TYPE_CHAR = "TYPE_CHAR"
TYPE_SPACE = "TYPE_SPACE"
TYPE_BACKSPACE = "TYPE_BACKSPACE"
TYPE_MOVE_LEFT = "TYPE_MOVE_LEFT"
TYPE_MOVE_RIGHT = "TYPE_MOVE_RIGHT"
TYPE_MOVE_UP = "TYPE_MOVE_UP"
TYPE_MOVE_DOWN = "TYPE_MOVE_DOWN"
TYPE_TOGGLE_CASE = "TYPE_TOGGLE_CASE"
TYPE_SUBMIT = "TYPE_SUBMIT"


def _is_single_char_label(s):
    return (s is not None) and (len(s) == 1)


def _is_ascii_letter(c):
    o = ord(c)
    return (ord("a") <= o <= ord("z")) or (ord("A") <= o <= ord("Z"))


def _invert_ascii_case(c):
    o = ord(c)
    if ord("a") <= o <= ord("z"):
        return chr(o - ord("a") + ord("A"))
    if ord("A") <= o <= ord("Z"):
        return chr(o - ord("A") + ord("a"))
    return c


class InputronicKeyboard:
    """
    MicroPython driver for the Soldered Inputronic Keyboard (TI TCA8418).

    Polling model:
      - events_available()
      - read_mapped_event() -> (is_release, row, col, label)
    """

    def __init__(self, i2c=None, address=INPUTRONIC_KBD_DEFAULT_ADDR, rows=8, cols=10):
        if i2c is not None:
            self.i2c = i2c
        else:
            # Mirror BMP280 style: auto-pins only for known boards
            if uname().sysname in ("esp32", "esp8266", "Soldered Dasduino CONNECTPLUS"):
                self.i2c = I2C(0, scl=Pin(22), sda=Pin(21))
            else:
                raise Exception("Board not recognized, pass an initialized I2C object")

        self.address = address

        # Internal state
        self._key_state = [[False for _ in range(10)] for _ in range(8)]
        self._last_label = None
        self._last_row = 0
        self._last_col = 0
        self._has_last = False

        self._active_id = IKMAP_UPPER
        self._active_map = INPUTRONIC_KEYMAP_UPPER

        # Init chip
        ok = self.begin(rows=rows, cols=cols)
        if not ok:
            raise Exception(
                "InputronicKeyboard initialization failed! Check wiring and I2C address."
            )

    # ----------------------------
    # Low-level I2C helpers
    # ----------------------------

    def _write8(self, reg, val):
        self.i2c.writeto(self.address, bytes([reg & 0xFF, val & 0xFF]))
        time.sleep_us(100)

    def _read8(self, reg):
        self.i2c.writeto(self.address, bytes([reg & 0xFF]))
        return self.i2c.readfrom(self.address, 1)[0]

    # ----------------------------
    # Initialization / configuration
    # ----------------------------

    def begin(self, rows=8, cols=10):
        # Start in UPPER
        self._active_id = IKMAP_UPPER
        self._active_map = INPUTRONIC_KEYMAP_UPPER

        # Reset internal state
        for r in range(8):
            for c in range(10):
                self._key_state[r][c] = False
        self._last_label = None
        self._last_row = 0
        self._last_col = 0
        self._has_last = False

        # Configure GPIO directions: inputs
        try:
            self._write8(TCA8418_REG_GPIO_DIR_1, 0x00)
            self._write8(TCA8418_REG_GPIO_DIR_2, 0x00)
            self._write8(TCA8418_REG_GPIO_DIR_3, 0x00)

            # Enable GPI event generation (OK for polling)
            self._write8(TCA8418_REG_GPI_EM_1, 0xFF)
            self._write8(TCA8418_REG_GPI_EM_2, 0xFF)
            self._write8(TCA8418_REG_GPI_EM_3, 0xFF)

            # Interrupt level defaults
            self._write8(TCA8418_REG_GPIO_INT_LVL_1, 0x00)
            self._write8(TCA8418_REG_GPIO_INT_LVL_2, 0x00)
            self._write8(TCA8418_REG_GPIO_INT_LVL_3, 0x00)

            # Disable interrupt outputs in polling mode
            self._write8(TCA8418_REG_GPIO_INT_EN_1, 0x00)
            self._write8(TCA8418_REG_GPIO_INT_EN_2, 0x00)
            self._write8(TCA8418_REG_GPIO_INT_EN_3, 0x00)

            # Enable debounce (disable bits = 0)
            self._write8(TCA8418_REG_DEBOUNCE_DIS_1, 0x00)
            self._write8(TCA8418_REG_DEBOUNCE_DIS_2, 0x00)
            self._write8(TCA8418_REG_DEBOUNCE_DIS_3, 0x00)

            if not self.configure_matrix(rows, cols):
                return False

            self.clear_events()
            return True
        except OSError:
            return False

    def configure_matrix(self, rows=8, cols=10):
        if rows < 1 or cols < 1 or rows > 8 or cols > 10:
            return False

        # Row mask in KP_GPIO_1 (bit0=row0)
        rmask = 0
        for _ in range(rows):
            rmask = ((rmask << 1) | 1) & 0xFF
        self._write8(TCA8418_REG_KP_GPIO_1, rmask)

        # Col mask 0..7 in KP_GPIO_2
        cmask = 0
        for _ in range(min(cols, 8)):
            cmask = ((cmask << 1) | 1) & 0xFF
        self._write8(TCA8418_REG_KP_GPIO_2, cmask)

        # Col 8..9 in KP_GPIO_3 bits 0..1
        if cols > 8:
            self._write8(TCA8418_REG_KP_GPIO_3, 0x01 if cols == 9 else 0x03)
        else:
            self._write8(TCA8418_REG_KP_GPIO_3, 0x00)

        return True

    # ----------------------------
    # FIFO / event handling
    # ----------------------------

    def events_available(self):
        try:
            ec = self._read8(TCA8418_REG_KEY_LCK_EC)
            return ec & 0x0F
        except OSError:
            return 0

    def available(self):
        return self.events_available() > 0

    def read_event_raw(self):
        try:
            return self._read8(TCA8418_REG_KEY_EVENT_A)
        except OSError:
            return 0

    def clear_events(self):
        cnt = 0
        while True:
            e = self.read_event_raw()
            if e == 0:
                break
            cnt += 1

        # clear-on-read GPIO INT status regs
        try:
            _ = self._read8(TCA8418_REG_GPIO_INT_STAT_1)
            _ = self._read8(TCA8418_REG_GPIO_INT_STAT_2)
            _ = self._read8(TCA8418_REG_GPIO_INT_STAT_3)
            # clear global INT flags
            self._write8(
                TCA8418_REG_INT_STAT, (TCA8418_STAT_GPI_INT | TCA8418_STAT_K_INT)
            )
        except OSError:
            pass

        return cnt

    # ----------------------------
    # Label helpers
    # ----------------------------

    def get_key_label(self, row, col):
        if row < 0 or row >= 8 or col < 0 or col >= 10:
            return None
        return self._active_map[row][col]

    def get_key_label_from_event(self, event_code):
        code = event_code & 0x7F
        if code == 0 or code > 0x50:
            return None
        idx = code - 1
        row = idx // 10
        col = idx % 10
        return self.get_key_label(row, col)

    # ----------------------------
    # Mapped read
    # ----------------------------

    def read_mapped_event(self):
        """
        Read one FIFO event and return tuple:
          (is_release: bool, row: int, col: int, label: str|None)

        Returns None if no event.
        """
        if self.events_available() == 0:
            return None

        evt = self.read_event_raw()
        if evt == 0:
            return None

        ok, is_release, row, col, label = self.process_event_code(evt)
        if not ok:
            return None
        return (is_release, row, col, label)

    def process_event_code(self, event_code):
        if event_code == 0:
            return (False, True, 0, 0, None)

        # MSB=1 press, MSB=0 release
        is_press = (event_code & 0x80) != 0
        is_release = not is_press

        code = event_code & 0x7F
        if code == 0 or code > 0x50:
            return (False, True, 0, 0, None)

        k = code - 1
        row = k // 10
        col = k % 10

        label = self.get_key_label(row, col)

        # Update held state + last press
        if 0 <= row < 8 and 0 <= col < 10:
            self._key_state[row][col] = is_press
            if is_press:
                self._last_label = label
                self._last_row = row
                self._last_col = col
                self._has_last = True

        # CAPS toggles on press only; refresh label after toggle
        if (label is not None) and is_press and (label == "CAPS"):
            self.toggle_active_keymap()
            label = self.get_key_label(row, col)

        return (True, is_release, row, col, label)

    # ----------------------------
    # Label -> char (SHIFT support)
    # ----------------------------

    def label_to_char(self, label, apply_shift=True):
        """
        If label is single character, returns printable char (len=1).
        Otherwise returns None.

        SHIFT behavior:
          - If SHIFT held:
              letters -> invert case
              non-letters -> shiftmap table
        """
        if not _is_single_char_label(label):
            return None

        ch = label[0]

        if apply_shift and self.is_key_pressed("SHIFT"):
            if _is_ascii_letter(ch):
                ch = _invert_ascii_case(ch)
            else:
                shifted = inputronic_apply_shift(ch)
                if shifted is not None:
                    ch = shifted

        return ch

    # ----------------------------
    # Pressed-state helpers
    # ----------------------------

    def is_key_pressed_rc(self, row, col):
        if row < 0 or row >= 8 or col < 0 or col >= 10:
            return False
        return self._key_state[row][col]

    def find_key_by_label(self, label):
        if not label:
            return None

        # exact match
        for r in range(8):
            for c in range(10):
                l = self._active_map[r][c]
                if l is None:
                    continue
                if l == label:
                    return (r, c)

        # one-char fallback by value
        if len(label) == 1:
            ch = label[0]
            for r in range(8):
                for c in range(10):
                    l = self._active_map[r][c]
                    if l is not None and len(l) == 1 and l[0] == ch:
                        return (r, c)

        return None

    def is_key_pressed(self, label_or_char):
        if label_or_char is None:
            return False
        if isinstance(label_or_char, int):
            # if someone passes ord()
            label_or_char = chr(label_or_char)
        if isinstance(label_or_char, str) and len(label_or_char) == 1:
            label = label_or_char
        else:
            label = label_or_char

        pos = self.find_key_by_label(label)
        if pos is None:
            return False
        r, c = pos
        return self._key_state[r][c]

    def any_key_pressed(self):
        for r in range(8):
            for c in range(10):
                if self._key_state[r][c]:
                    return True
        return False

    def get_held_count(self):
        n = 0
        for r in range(8):
            for c in range(10):
                if self._key_state[r][c]:
                    n += 1
        return n

    # ----------------------------
    # Last / current key helpers
    # ----------------------------

    def get_last_key_label(self):
        return self._last_label if self._has_last else None

    def get_last_key(self):
        if not self._has_last:
            return None
        return (self._last_row, self._last_col, self._last_label)

    def get_current_key_label(self):
        cur = self.get_current_key()
        return cur[2] if cur else None

    def get_current_key(self):
        for r in range(8):
            for c in range(10):
                if self._key_state[r][c]:
                    return (r, c, self._active_map[r][c])
        return None

    # ----------------------------
    # Keymap control
    # ----------------------------

    def set_active_keymap(self, keymap_id):
        self._active_id = IKMAP_LOWER if keymap_id == IKMAP_LOWER else IKMAP_UPPER
        self._active_map = (
            INPUTRONIC_KEYMAP_LOWER
            if self._active_id == IKMAP_LOWER
            else INPUTRONIC_KEYMAP_UPPER
        )

    def toggle_active_keymap(self):
        self.set_active_keymap(
            IKMAP_LOWER if self._active_id == IKMAP_UPPER else IKMAP_UPPER
        )

    def get_active_keymap(self):
        return self._active_id

    # ----------------------------
    # Convenience input methods
    # ----------------------------

    def string_input(
        self, max_len=64, timeout_ms=0, end_label="ENTER", backspace_label="BACK"
    ):
        """
        Blocking string input. Returns collected string.
        timeout_ms=0 means no timeout.
        """
        if max_len <= 0:
            return ""

        out = []
        t0 = time.ticks_ms()

        def expired():
            return (timeout_ms > 0) and (
                time.ticks_diff(time.ticks_ms(), t0) >= timeout_ms
            )

        while True:
            if expired():
                return "".join(out)

            ev = self.read_mapped_event()
            if ev is None:
                time.sleep_ms(1)
                continue

            is_release, row, col, label = ev
            if is_release or label is None:
                continue

            if end_label and label == end_label:
                return "".join(out)

            if backspace_label and label == backspace_label:
                if out:
                    out.pop()
                continue

            if label == "SPACE":
                if len(out) < max_len:
                    out.append(" ")
                continue

            ch = self.label_to_char(label, apply_shift=True)
            if ch is not None and len(out) < max_len:
                out.append(ch)

    def type_on(self, cb=None, user=None, end_label=None, backspace_label="BACK"):
        """
        Blocking "type mode". cb signature:
          cb(ev_type, ch, row, col, label, user)

        If cb is None: prints to stdout.
        """

        def default_cb(ev_type, ch, row, col, label, user):
            # MicroPython: use print with end=
            if ev_type == TYPE_CHAR:
                print(ch, end="")
            elif ev_type == TYPE_SPACE:
                print(" ", end="")
            elif ev_type == TYPE_BACKSPACE:
                # Terminal behaviour may vary; simple representation:
                print("\b \b", end="")
            elif ev_type == TYPE_TOGGLE_CASE:
                print("[CASE]", end="")
            elif ev_type == TYPE_MOVE_LEFT:
                print("[LEFT]", end="")
            elif ev_type == TYPE_MOVE_RIGHT:
                print("[RIGHT]", end="")
            elif ev_type == TYPE_MOVE_UP:
                print("[UP]", end="")
            elif ev_type == TYPE_MOVE_DOWN:
                print("[DOWN]", end="")
            elif ev_type == TYPE_SUBMIT:
                print("\r\n[SUBMIT]")

        handler = cb if cb is not None else default_cb

        while True:
            ev = self.read_mapped_event()
            if ev is None:
                time.sleep_ms(1)
                continue

            is_release, row, col, label = ev
            if is_release or label is None:
                continue

            # submit
            if end_label and label == end_label:
                handler(TYPE_SUBMIT, None, row, col, label, user)
                return

            # backspace
            if backspace_label and label == backspace_label:
                handler(TYPE_BACKSPACE, None, row, col, label, user)
                continue

            # CAPS
            if label == "CAPS":
                handler(TYPE_TOGGLE_CASE, None, row, col, label, user)
                continue

            # nav
            if label == "LEFT":
                handler(TYPE_MOVE_LEFT, None, row, col, label, user)
                continue
            if label == "RIGHT":
                handler(TYPE_MOVE_RIGHT, None, row, col, label, user)
                continue
            if label == "UP":
                handler(TYPE_MOVE_UP, None, row, col, label, user)
                continue
            if label == "DOWN":
                handler(TYPE_MOVE_DOWN, None, row, col, label, user)
                continue

            # space
            if label == "SPACE":
                handler(TYPE_SPACE, " ", row, col, label, user)
                continue

            # printable
            ch = self.label_to_char(label, apply_shift=True)
            if ch is not None:
                handler(TYPE_CHAR, ch, row, col, label, user)
