# =============================================================================
# tft_display_pi.py — EDEMI Smart Glasses
# ST7789P3 TFT driver — 76x284 bar display
# Uses lgpio (NOT RPi.GPIO — broken on Trixie)
# Uses spidev for SPI
#
# Correct parameters from Arduino forum LODAM (Jan 2026) — confirmed working
# on same AliExpress display (ESP32 + community verified May 2026)
#
# Wiring (BCM GPIO):
#   VCC  → Pin 1  (3.3V)
#   GND  → Pin 6  (GND)
#   SCL  → GPIO11 (SPI0_SCLK)
#   SDA  → GPIO10 (SPI0_MOSI)
#   RST  → GPIO25
#   DC   → GPIO24
#   CS   → GPIO8  (SPI0_CE0)
#   BL   → GPIO13 (Pin 33) — input mode, TFT self-drives to full brightness
# =============================================================================

import time
import spidev
import lgpio
from PIL import Image, ImageDraw, ImageFont

# =============================================================================
# DISPLAY CONSTANTS — DO NOT CHANGE
# =============================================================================

TFT_WIDTH   = 76
TFT_HEIGHT  = 284

# BCM GPIO pins
PIN_RST = 25
PIN_DC  = 24
PIN_BL  = 13

# Correct offsets for portrait mode (rotation 0)
# Source: Arduino forum LODAM Jan 2026, confirmed working
COL_OFFSET = 82
ROW_OFFSET = 18

# MADCTL — BGR colour order, portrait
MADCTL_PORTRAIT = 0x08

# SPI
SPI_BUS   = 0
SPI_DEV   = 0
SPI_SPEED = 27000000  # 27MHz — confirmed working

# Colours (RGB565)
BLACK   = 0x0000
WHITE   = 0xFFFF
RED     = 0xF800
GREEN   = 0x07E0
BLUE    = 0x001F
YELLOW  = 0xFFE0
CYAN    = 0x07FF
MAGENTA = 0xF81F

# =============================================================================
# LOW LEVEL DRIVER
# =============================================================================

class ST7789Driver:
    def __init__(self):
        self._gpio = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self._gpio, PIN_RST)
        lgpio.gpio_claim_output(self._gpio, PIN_DC)
        lgpio.gpio_claim_input(self._gpio, PIN_BL)
        self._spi = spidev.SpiDev()
        self._spi.open(SPI_BUS, SPI_DEV)
        self._spi.max_speed_hz = SPI_SPEED
        self._spi.mode = 0
        self._reset()
        self._init_sequence()

    def _reset(self):
        lgpio.gpio_write(self._gpio, PIN_RST, 1)
        time.sleep(0.01)
        lgpio.gpio_write(self._gpio, PIN_RST, 0)
        time.sleep(0.01)
        lgpio.gpio_write(self._gpio, PIN_RST, 1)
        time.sleep(0.05)

    def _command(self, cmd):
        lgpio.gpio_write(self._gpio, PIN_DC, 0)
        self._spi.writebytes([cmd])

    def _data(self, data):
        lgpio.gpio_write(self._gpio, PIN_DC, 1)
        if isinstance(data, list):
            self._spi.writebytes(data)
        else:
            self._spi.writebytes([data])

    def _init_sequence(self):
        self._command(0xB2)
        self._data([0x0C, 0x0C, 0x00, 0x33, 0x33])
        self._command(0xB7)
        self._data(0x45)
        self._command(0xBB)
        self._data(0x35)
        self._command(0xC0)
        self._data(0x2C)
        self._command(0xC2)
        self._data(0x01)
        self._command(0xC3)
        self._data(0x19)
        self._command(0xC4)
        self._data(0x20)
        self._command(0xC6)
        self._data(0x0F)
        self._command(0xD0)
        self._data([0xA4, 0xA1])
        self._command(0xE0)
        self._data([0xD0, 0x10, 0x21, 0x14, 0x15,
                    0x2D, 0x41, 0x44, 0x4F, 0x28,
                    0x0E, 0x0C, 0x1D, 0x1F])
        self._command(0xE1)
        self._data([0xD0, 0x0F, 0x1B, 0x0D, 0x0D,
                    0x26, 0x42, 0x54, 0x50, 0x3E,
                    0x1A, 0x18, 0x22, 0x25])
        self._command(0x36)
        self._data(MADCTL_PORTRAIT)
        self._command(0x3A)
        self._data(0x05)
        self._command(0x20)
        self._command(0x11)
        time.sleep(0.12)
        self._command(0x29)
        time.sleep(0.05)

    def _set_window(self, x0, y0, x1, y1):
        self._command(0x2A)
        self._data([(x0 + COL_OFFSET) >> 8,
                    (x0 + COL_OFFSET) & 0xFF,
                    (x1 + COL_OFFSET) >> 8,
                    (x1 + COL_OFFSET) & 0xFF])
        self._command(0x2B)
        self._data([(y0 + ROW_OFFSET) >> 8,
                    (y0 + ROW_OFFSET) & 0xFF,
                    (y1 + ROW_OFFSET) >> 8,
                    (y1 + ROW_OFFSET) & 0xFF])
        self._command(0x2C)

    def fill_screen(self, colour):
        self._set_window(0, 0, TFT_WIDTH - 1, TFT_HEIGHT - 1)
        hi  = colour >> 8
        lo  = colour & 0xFF
        buf = [hi, lo] * (TFT_WIDTH * TFT_HEIGHT)
        lgpio.gpio_write(self._gpio, PIN_DC, 1)
        chunk = 4096
        for i in range(0, len(buf), chunk):
            self._spi.writebytes(buf[i:i + chunk])

    def display_image(self, img):
        if img.size != (TFT_WIDTH, TFT_HEIGHT):
            img = img.resize((TFT_WIDTH, TFT_HEIGHT))
        self._set_window(0, 0, TFT_WIDTH - 1, TFT_HEIGHT - 1)
        lgpio.gpio_write(self._gpio, PIN_DC, 1)
        pixels = img.convert('RGB').tobytes()
        buf    = []
        for i in range(0, len(pixels), 3):
            r = pixels[i]
            g = pixels[i + 1]
            b = pixels[i + 2]
            colour = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            buf.append(colour >> 8)
            buf.append(colour & 0xFF)
        chunk = 4096
        for i in range(0, len(buf), chunk):
            self._spi.writebytes(buf[i:i + chunk])

    def cleanup(self):
        self._spi.close()
        lgpio.gpiochip_close(self._gpio)


# =============================================================================
# HIGH LEVEL TFT DISPLAY — used by main.py
# =============================================================================

class TFTDisplay:
    def __init__(self):
        self.driver      = ST7789Driver()
        self.suggestions = []
        self.selected    = 0
        self._font_large = None
        self._font_small = None
        self._load_fonts()
        self.driver.fill_screen(BLACK)
        open("/tmp/edemi.log", "a").write("TFT display initialized\n")

    def _load_fonts(self):
        try:
            self._font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            self._font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        except:
            self._font_large = ImageFont.load_default()
            self._font_small = ImageFont.load_default()

    def show_suggestions(self, suggestions, selected=0):
        self.suggestions = suggestions
        self.selected    = selected
        self._render()

    def scroll_up(self):
        if self.selected > 0:
            self.selected -= 1
            self._render()

    def scroll_down(self):
        if self.selected < len(self.suggestions) - 1:
            self.selected += 1
            self._render()

    def get_selected(self):
        if self.suggestions:
            return self.suggestions[self.selected]
        return ""

    def clear(self):
        self.suggestions = []
        self.selected    = 0
        self.driver.fill_screen(BLACK)

    def show_message(self, message, colour=WHITE):
        img  = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        words = message.split()
        lines = []
        line  = ""
        for word in words:
            test = line + word + " "
            if len(test) * 7 > TFT_WIDTH:
                lines.append(line.strip())
                line = word + " "
            else:
                line = test
        if line:
            lines.append(line.strip())
        y = (TFT_HEIGHT - len(lines) * 16) // 2
        for l in lines:
            w = len(l) * 7
            x = (TFT_WIDTH - w) // 2
            draw.text((x, y), l, font=self._font_small,
                      fill=self._colour565_to_rgb(colour))
            y += 16
        self.driver.display_image(img)

    def _render(self):
        img  = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        item_height = 40
        padding     = 4
        for i, text in enumerate(self.suggestions[:7]):
            y = i * item_height + padding
            if i == self.selected:
                draw.rectangle([0, y, TFT_WIDTH, y + item_height - 2],
                                fill=(255, 255, 255))
                text_colour = (0, 0, 0)
            else:
                text_colour = (200, 200, 200)
            words = text.split()
            line  = ""
            lines = []
            for word in words:
                test = line + word + " "
                if len(test) * 6 > TFT_WIDTH - 4:
                    lines.append(line.strip())
                    line = word + " "
                else:
                    line = test
            if line:
                lines.append(line.strip())
            ty = y + 4
            for l in lines[:2]:
                draw.text((2, ty), l, font=self._font_small,
                           fill=text_colour)
                ty += 14
        self.driver.display_image(img)

    def _colour565_to_rgb(self, colour565):
        r = (colour565 >> 11) & 0x1F
        g = (colour565 >> 5)  & 0x3F
        b =  colour565        & 0x1F
        return (r << 3, g << 2, b << 3)

    def cleanup(self):
        self.driver.cleanup()
