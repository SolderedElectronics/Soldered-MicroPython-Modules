# FILE: WS2812Grid.py
# AUTHOR: Josip Šimun Kuči @ Soldered
# BRIEF: MicroPython driver for the Soldered WS2812B 8x8 LED grid.
#        Provides (x, y) coordinate interface over a serpentine WS2812B grid.
#        Even rows run left-to-right, odd rows run right-to-left.
#        Uses MicroPython's built-in neopixel module for LED control.
# WORKS WITH: Soldered WS2812B LED Grid: www.soldered.com
# LAST UPDATED: 2026-05-12

import neopixel
from machine import Pin

WS2812GRID_DEFAULT_WIDTH  = 8
WS2812GRID_DEFAULT_HEIGHT = 8


class WS2812Grid:
    """
    MicroPython driver for the Soldered WS2812B 8x8 LED grid.

    Supports grids of any size that are multiples of 8 panels.
    (0, 0) is top-left. X increases to the right, Y increases downward.

    Usage:
        from machine import Pin
        from WS2812Grid import WS2812Grid

        grid = WS2812Grid(Pin(6, Pin.OUT))
        grid.begin()
        grid.setBrightness(40)
        grid.setPixel(0, 0, 255, 0, 0)
        grid.show()
    """

    def __init__(self, pin, width=WS2812GRID_DEFAULT_WIDTH, height=WS2812GRID_DEFAULT_HEIGHT):
        """
        Initialize the WS2812B grid driver.

        :param pin:    machine.Pin object connected to the grid data line
        :param width:  Number of columns (default 8)
        :param height: Number of rows (default 8)
        """
        self._width = width
        self._height = height
        self._brightness = 255
        self._np = neopixel.NeoPixel(pin, width * height)

    def begin(self):
        """Initialize the LED driver. Clears the display and calls show()."""
        self.clear()
        self.show()

    # ── Brightness ────────────────────────────────────────────────────────────

    def setBrightness(self, brightness):
        """
        Set overall brightness scale applied when setting pixels.

        :param brightness: 0 (off) to 255 (full brightness)
        """
        self._brightness = max(0, min(255, brightness))

    # ── Pixel control ─────────────────────────────────────────────────────────

    def setPixel(self, x, y, r_or_color, g=None, b=None):
        """
        Set a single LED by grid coordinates.

        Two calling conventions:
          setPixel(x, y, r, g, b)          — separate RGB components
          setPixel(x, y, color)             — packed 0x00RRGGBB color

        Call show() afterwards to push changes to hardware.
        """
        idx = self.xyToIndex(x, y)
        if idx == 0xFFFF:
            return
        if g is None:
            color = r_or_color
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
        else:
            r = r_or_color
        self._np[idx] = self._scaledColor(r, g, b)

    def getPixel(self, x, y):
        """
        Read back the stored color of a single LED.

        :return: Packed color (0x00RRGGBB), or 0 if coordinates are out of range
        """
        idx = self.xyToIndex(x, y)
        if idx == 0xFFFF:
            return 0
        r, g, b = self._np[idx]
        return (r << 16) | (g << 8) | b

    def fill(self, r_or_color, g=None, b=None):
        """
        Fill every LED with the same color.

        Two calling conventions:
          fill(r, g, b)    — separate RGB components
          fill(color)      — packed 0x00RRGGBB color

        Call show() afterwards to push changes to hardware.
        """
        if g is None:
            color = r_or_color
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
        else:
            r = r_or_color
        self._np.fill(self._scaledColor(r, g, b))

    def clear(self):
        """Turn all LEDs off (does not call show())."""
        self._np.fill((0, 0, 0))

    def show(self):
        """Push buffered color data to the hardware."""
        self._np.write()

    # ── Index mapping ─────────────────────────────────────────────────────────

    def xyToIndex(self, x, y):
        """
        Convert (x, y) grid coordinates to a linear LED index.

        Panels are 8x8 and chained column-first. Within each panel wiring is
        serpentine: even local rows left-to-right, odd rows right-to-left.

        :return: LED index (0 to width*height-1), or 0xFFFF if out of range
        """
        if x >= self._width or y >= self._height:
            return 0xFFFF

        PANEL_SIZE = 8
        panelCol = x // PANEL_SIZE
        panelRow = y // PANEL_SIZE
        localX = x % PANEL_SIZE
        localY = y % PANEL_SIZE

        numPanelRows = self._height // PANEL_SIZE
        panelIndex = panelCol * numPanelRows + panelRow
        ledBase = panelIndex * (PANEL_SIZE * PANEL_SIZE)

        if localY % 2 == 0:
            localIndex = localY * PANEL_SIZE + localX
        else:
            localIndex = localY * PANEL_SIZE + (PANEL_SIZE - 1 - localX)

        return ledBase + localIndex

    # ── Static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def Color(r, g, b):
        """
        Pack RGB components into a 32-bit color value (0x00RRGGBB).

        :return: Packed color integer
        """
        return (r << 16) | (g << 8) | b

    # ── Private helpers ───────────────────────────────────────────────────────

    def _scaledColor(self, r, g, b):
        if self._brightness == 255:
            return (r, g, b)
        br = self._brightness
        return (r * br // 255, g * br // 255, b * br // 255)
