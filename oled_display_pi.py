from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageFont
import os
import threading

OLED_WIDTH   = 128
OLED_HEIGHT  = 64
I2C_PORT     = 1
I2C_ADDRESS  = 0x3C
CLEAR_AFTER  = 10  # seconds


class TFTDisplay:

    def __init__(self):
        serial = i2c(port=I2C_PORT, address=I2C_ADDRESS)
        self.device      = ssd1306(serial)
        self.device.contrast(255)
        self.suggestions = []
        self.selected    = 0
        self._lock       = threading.Lock()
        self._clear_timer = None
        self._load_fonts()
        print("OLED display initialized")

    def _load_fonts(self):
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
        self._font = None
        for path in font_paths:
            if os.path.exists(path):
                try:
                    self._font = ImageFont.truetype(path, 12)
                    break
                except Exception:
                    pass
        if not self._font:
            self._font = ImageFont.load_default()

    def _cancel_clear_timer(self):
        if self._clear_timer is not None:
            self._clear_timer.cancel()
            self._clear_timer = None

    def _schedule_clear(self):
        self._cancel_clear_timer()
        self._clear_timer = threading.Timer(CLEAR_AFTER, self.clear)
        self._clear_timer.daemon = True
        self._clear_timer.start()

    def _show_text(self, message):
        words = message.split()
        lines = []
        line  = ""
        for word in words:
            test = line + word + " "
            if len(test) > 18:
                lines.append(line.strip())
                line = word + " "
            else:
                line = test
        if line:
            lines.append(line.strip())

        line_h  = 14
        total_h = len(lines) * line_h
        y_start = (OLED_HEIGHT - total_h) // 2

        with canvas(self.device) as draw:
            for i, l in enumerate(lines):
                try:
                    bbox = draw.textbbox((0, 0), l, font=self._font)
                    w    = bbox[2] - bbox[0]
                except AttributeError:
                    w = len(l) * 6
                x = (OLED_WIDTH - w) // 2
                y = y_start + i * line_h
                draw.text((x, y), l, font=self._font, fill="white")

    def show_message(self, message, colour=None):
        self._cancel_clear_timer()
        self._show_text(message)
        self._schedule_clear()

    def show_suggestions(self, suggestions, selected=0):
        self.suggestions = suggestions
        self.selected    = selected

    def scroll_up(self):
        if self.selected > 0:
            self.selected -= 1

    def scroll_down(self):
        if self.selected < len(self.suggestions) - 1:
            self.selected += 1

    def get_selected(self):
        if self.suggestions:
            return self.suggestions[self.selected]
        return ""

    def clear(self):
        self._cancel_clear_timer()
        self.suggestions = []
        self.selected    = 0
        try:
            with canvas(self.device) as draw:
                draw.rectangle(
                    [(0, 0), (OLED_WIDTH - 1, OLED_HEIGHT - 1)],
                    fill="black"
                )
        except Exception as e:
            open("/tmp/edemi.log", "a").write("OLED clear error: " + str(e) + "\n")

    def show_reply(self, message):
        self.show_message(message)

    def cleanup(self):
        self._cancel_clear_timer()
        try:
            self.device.cleanup()
        except Exception:
            pass
