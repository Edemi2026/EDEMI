# =============================================================================
# ar_display_pi.py — EDEMI Smart Glasses (PI VERSION)
# Terminal based AR display using curses
# Works on Pi OS Lite without desktop or pygame drivers
# Outputs to HDMI terminal — deaf person sees this
# =============================================================================

import curses
import time
import threading
from config import (
    MAX_SUGGESTIONS,
    ENV_ALERT_DURATION,
    RUNNING_ON_PI,
)
from settings_manager import get_setting


class ARDisplay:
    """
    Terminal based AR display for Pi Zero 2W.
    Uses curses for colored text display on HDMI terminal.
    """

    def __init__(self, tft=None):
        self.tft              = tft
        self.suggestions      = []
        self.selected_index   = 0
        self.last_speech      = ""
        self.speech_text      = "Listening..."
        self.status_text      = "Listening..."
        self.menu_open        = False
        self.menu_items       = []
        self.menu_index       = 0
        self.emergency_mode   = False
        self.reply_text       = ""
        self.countdown_secs   = 0
        self.auto_pending     = None
        self.alert_message    = ""
        self.alert_level      = ""
        self.alert_end_time   = 0
        self.confirm_text     = ""
        self.confirm_end_time = 0
        self.wifi_status      = "Hotspot"
        self._lock            = threading.Lock()
        self._running         = True
        self._stdscr          = None

        # Initialize curses
        self._stdscr = curses.initscr()
        curses.start_color()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        self._stdscr.keypad(True)
        self._stdscr.nodelay(True)

        # Color pairs
        curses.init_pair(1, curses.COLOR_GREEN,  curses.COLOR_BLACK)  # Green
        curses.init_pair(2, curses.COLOR_WHITE,  curses.COLOR_BLACK)  # White
        curses.init_pair(3, curses.COLOR_CYAN,   curses.COLOR_BLACK)  # Cyan
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Yellow
        curses.init_pair(5, curses.COLOR_RED,    curses.COLOR_BLACK)  # Red
        curses.init_pair(6, curses.COLOR_BLACK,  curses.COLOR_GREEN)  # Selected
        curses.init_pair(7, curses.COLOR_BLUE,   curses.COLOR_BLACK)  # Blue

        self.GREEN    = curses.color_pair(1)
        self.WHITE    = curses.color_pair(2)
        self.CYAN     = curses.color_pair(3)
        self.YELLOW   = curses.color_pair(4)
        self.RED      = curses.color_pair(5)
        self.SELECTED = curses.color_pair(6)
        self.BLUE     = curses.color_pair(7)

        self.height, self.width = self._stdscr.getmaxyx()

        # Apply text size from settings
        size = get_setting("ar_text_size", "Medium")
        self._text_bold = curses.A_BOLD if size in ["Medium", "Large"] else 0
        self._text_attr = curses.A_BOLD if size == "Large" else 0

    # =========================================================================
    # DRAWING HELPERS
    # =========================================================================

    def _safe_addstr(self, y, x, text, attr=0):
        """Safely add string — ignore out of bounds errors."""
        try:
            if y < self.height and x < self.width:
                max_len = self.width - x - 1
                self._stdscr.addstr(y, x, text[:max_len], attr)
        except curses.error:
            pass

    def _draw_line(self, y, char="─"):
        """Draw horizontal line."""
        try:
            self._stdscr.addstr(y, 0, char * (self.width - 1), self.CYAN)
        except curses.error:
            pass

    def _draw_frame(self):
        """Draw complete AR display frame."""
        self._stdscr.erase()
        now = time.time()

        # STATUS BAR (row 0)
        time_str = time.strftime("%H:%M:%S")
        date_str = time.strftime("%a %d %b")
        status   = f" EDEMI  |  Powered  |  {self.wifi_status}  |  {date_str}  |  {time_str} "
        self._safe_addstr(0, 0, status.ljust(self.width - 1), self.GREEN | curses.A_BOLD)

        # ENVIRONMENT ALERT (row 2)
        if self.alert_message and now < self.alert_end_time:
            blink = int(now * 2) % 2
            dot   = "*" if blink else "o"
            color = self.RED    if self.alert_level == "danger"  else \
                    self.YELLOW if self.alert_level == "caution" else self.WHITE
            self._safe_addstr(2, 0, f" {dot} {self.alert_message}", color | curses.A_BOLD)
        else:
            if self.alert_message and now >= self.alert_end_time:
                self.alert_message = ""

        # DIVIDER
        self._draw_line(3)

        # SPEECH ZONE (rows 4-10)
        self._safe_addstr(4, 0, " LIVE SPEECH", self.CYAN | curses.A_BOLD)

        if self.menu_open:
            self._draw_menu()
        elif self.emergency_mode:
            self._draw_emergency()
        else:
            words = self.speech_text.split()
            lines = []
            line  = ""
            max_w = self.width - 3
            for word in words:
                test = (line + " " + word).strip()
                if len(test) <= max_w:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)
            for i, ln in enumerate(lines[:4]):
                self._safe_addstr(5 + i, 1, f" {ln}", self.WHITE | self._text_bold)

        # DIVIDER
        self._draw_line(11)

        # SUGGESTIONS ZONE (rows 12-18)
        self._safe_addstr(12, 0, " SUGGESTED REPLIES", self.CYAN | curses.A_BOLD)

        if self.auto_pending:
            self._safe_addstr(13, 1,
                f" AUTO: \"{self.auto_pending}\"  |  Pad 4 cancel",
                self.YELLOW)

        elif self.confirm_text and now < self.confirm_end_time:
            self._safe_addstr(13, 1, " REPLY SENT", self.GREEN | curses.A_BOLD)
            self._safe_addstr(14, 1, f" \"{self.confirm_text}\"", self.WHITE)

        elif self.suggestions:
            for i, text in enumerate(self.suggestions[:MAX_SUGGESTIONS]):
                is_sel = (i == self.selected_index)
                prefix = f" > [{i+1}] " if is_sel else f"   [{i+1}] "
                attr   = self.SELECTED | curses.A_BOLD if is_sel else self.WHITE
                self._safe_addstr(13 + i, 0, f"{prefix}{text}", attr)

        else:
            self._safe_addstr(13, 1, " Waiting for speech...", self.BLUE)

        # DIVIDER
        self._draw_line(19)

        # BOTTOM STATUS (rows 20-22)
        if self.reply_text:
            self._safe_addstr(20, 1,
                f" YOUR REPLY -> \"{self.reply_text}\"",
                self.GREEN)
            if self.countdown_secs > 0:
                self._safe_addstr(21, 1,
                    f" Clears in {self.countdown_secs}s",
                    self.YELLOW)
        else:
            self._safe_addstr(20, 1, f" {self.status_text}", self.BLUE)

        # Touch pad hints
        hints = " Up:Pad1  Down:Pad2  Select:Pad3  ClearTFT:Pad4  ClearSpk:Pad5  Menu:HoldPad6"
        self._safe_addstr(self.height - 1, 0, hints[:self.width - 1], self.BLUE)

        self._stdscr.refresh()

    def _draw_menu(self):
        """Draw menu overlay."""
        self._safe_addstr(5, 2, "--- MENU ---", self.GREEN | curses.A_BOLD)
        for i, item in enumerate(self.menu_items):
            is_sel = (i == self.menu_index)
            prefix = " > " if is_sel else "   "
            attr   = self.SELECTED | curses.A_BOLD if is_sel else self.WHITE
            self._safe_addstr(6 + i, 2, f"{prefix}{item}", attr)
        self._safe_addstr(6 + len(self.menu_items) + 1, 2,
            "Hold Pad6 to close", self.BLUE)

    def _draw_emergency(self):
        """Draw emergency overlay."""
        self._safe_addstr(5, 2, "EMERGENCY - Select reply:",
            self.RED | curses.A_BOLD)
        for i, reply in enumerate(self.suggestions):
            is_sel = (i == self.selected_index)
            prefix = " > " if is_sel else f" [{i+1}] "
            attr   = self.RED | curses.A_BOLD if is_sel else self.WHITE
            self._safe_addstr(6 + i, 2, f"{prefix}{reply}", attr)

    # =========================================================================
    # TFT HELPER — safe wrapper
    # =========================================================================

    def _tft_call(self, method, *args):
        """Safely call a TFT method — never crashes the UI if TFT fails."""
        if self.tft:
            try:
                getattr(self.tft, method)(*args)
            except Exception as e:
                open("/tmp/edemi.log", "a").write(f"TFT error ({method}): {e}\n")

    # =========================================================================
    # PUBLIC INTERFACE
    # =========================================================================

    def update_speech(self, text):
        with self._lock:
            self.last_speech  = text
            self.speech_text  = text

    def show_status(self, text):
        with self._lock:
            self.speech_text = text
            self.status_text = text

    def show_suggestions(self, reply_dict):
        if not reply_dict:
            return
        reply_type = reply_dict.get("reply_type")
        content    = reply_dict.get("content")

        # Determine reply to send — outside lock to avoid deadlock
        send_reply = None

        with self._lock:
            if reply_type == "emergency":
                self.emergency_mode = True
                self.suggestions    = content
                self.selected_index = 0

            elif reply_type == "auto_pending":
                self.auto_pending = content

            elif reply_type in ["auto_social", "auto_name",
                                 "auto_ack", "auto_unclear",
                                 "auto_ambiguous"]:
                self.auto_pending = None
                send_reply = content

            elif reply_type == "prompted":
                self.auto_pending   = None
                self.suggestions    = content[:MAX_SUGGESTIONS]
                self.selected_index = 0
                self.confirm_text   = ""

        # Send reply outside lock
        if send_reply:
            self._do_send_reply(send_reply)

    def update_environment(self, alert_dict):
        if not alert_dict:
            return
        with self._lock:
            self.alert_message  = alert_dict.get("message", "")
            self.alert_level    = alert_dict.get("level", "info")
            self.alert_end_time = time.time() + ENV_ALERT_DURATION / 1000.0

    def update_system_status(self, status):
        with self._lock:
            self.wifi_status = status.get("wifi", "Hotspot")

    def scroll_suggestions(self, direction):
        with self._lock:
            if self.menu_open:
                if direction == "up":
                    self.menu_index = max(0, self.menu_index - 1)
                else:
                    self.menu_index = min(len(self.menu_items) - 1, self.menu_index + 1)
            elif self.suggestions:
                if direction == "up":
                    self.selected_index = max(0, self.selected_index - 1)
                else:
                    self.selected_index = min(
                        len(self.suggestions) - 1, self.selected_index + 1)

    def confirm_selection(self):
        reply = None
        with self._lock:
            if self.menu_open:
                item = self.menu_items[self.menu_index]
                self.menu_open = False
            else:
                item = None

            if item:
                pass  # handled below
            elif self.emergency_mode and self.suggestions:
                reply = self.suggestions[self.selected_index]
                self.emergency_mode = False
            elif self.suggestions:
                reply = self.suggestions[self.selected_index]

        if item:
            self._execute_menu(item)
        elif reply:
            self._do_send_reply(reply)

    def clear_tft(self):
        with self._lock:
            if self.auto_pending:
                self.auto_pending = None
                return
            self.reply_text     = ""
            self.countdown_secs = 0
        self._tft_call("clear")

    def clear_speech(self):
        with self._lock:
            self.speech_text    = "Listening..."
            self.suggestions    = []
            self.selected_index = 0
            self.confirm_text   = ""
            self.auto_pending   = None

    def repeat_last_speech(self):
        with self._lock:
            if self.last_speech:
                self.speech_text = self.last_speech

    def show_menu(self, items, index):
        with self._lock:
            self.menu_open  = True
            self.menu_items = items
            self.menu_index = index

    def update_menu(self, items, index):
        with self._lock:
            self.menu_items = items
            self.menu_index = index

    def hide_menu(self):
        with self._lock:
            self.menu_open = False

    def show_emergency(self, replies):
        with self._lock:
            self.emergency_mode = True
            self.suggestions    = replies
            self.selected_index = 0

    def show_shutdown_screen(self):
        with self._lock:
            self.speech_text = "Shutting down EDEMI... Goodbye!"
            self.suggestions = []
        self._tft_call("show_message", "GOODBYE")
        self._draw_frame()
        time.sleep(2)

    def _do_send_reply(self, text):
        """Send reply to TFT and update UI state."""
        self._tft_call("show_message", text)
        with self._lock:
            self.reply_text       = text
            self.confirm_text     = text
            self.confirm_end_time = time.time() + 4.0
            self.suggestions      = []
            self.selected_index   = 0
            self.speech_text      = "Listening..."
            delay                 = get_setting("tft_clear_delay", 10)
            self.countdown_secs   = delay
        self._start_countdown(delay)

    def _start_countdown(self, seconds):
        def _tick(s):
            while s > 0 and self._running:
                time.sleep(1)
                s -= 1
                with self._lock:
                    self.countdown_secs = s
            with self._lock:
                if self.countdown_secs == 0:
                    self.reply_text  = ""
                    self.status_text = "Ready for next reply"
        t = threading.Thread(target=_tick, args=(seconds,), daemon=True)
        t.start()

    def _execute_menu(self, item):
        if item == "Resume":
            pass
        elif item == "Clear Conversation":
            with self._lock:
                self.speech_text    = "Listening..."
                self.suggestions    = []
                self.selected_index = 0
                self.confirm_text   = ""
            self._tft_call("clear")
        elif item == "Shutdown":
            self.show_shutdown_screen()
            threading.Timer(2.0, self._do_shutdown).start()

    def _take_screenshot(self):
        """Capture current AR display to file."""
        import subprocess
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"/home/smart-pi/edemi/screenshots/edemi_{ts}.png"
        try:
            import struct
            with open("/dev/fb0", "rb") as fb:
                raw = fb.read()
            from PIL import Image
            img = Image.frombytes("RGBA", (640, 480), raw, "raw", "BGRA")
            img.save(path)
            open("/tmp/edemi.log", "a").write("Screenshot saved: " + path + "\n")
        except Exception as e:
            open("/tmp/edemi.log", "a").write("Screenshot error: " + str(e) + "\n")

    def _do_shutdown(self):
        import subprocess
        try:
            subprocess.run(["sudo", "shutdown", "-h", "now"])
        except Exception as e:
            open("/tmp/edemi.log", "a").write(f"Shutdown error: {e}\n")

    # =========================================================================
    # MAIN LOOP
    # =========================================================================

    def run(self):
        """Main display loop."""
        try:
            while self._running:
                with self._lock:
                    self._draw_frame()

                # Keyboard input (PC simulation + physical keyboard on Pi)
                try:
                    key = self._stdscr.getch()
                    if key == curses.KEY_UP:
                        self.scroll_suggestions("up")
                    elif key == curses.KEY_DOWN:
                        self.scroll_suggestions("down")
                    elif key == ord('\n'):
                        self.confirm_selection()
                    elif key == ord('c'):
                        self.clear_tft()
                    elif key == ord('x'):
                        self.clear_speech()
                    elif key == ord('r'):
                        self.repeat_last_speech()
                    elif key == ord('m'):
                        self.show_menu(
                            ["Resume", "Clear Conversation", "Shutdown"], 0)
                    elif key == 27:  # Escape
                        self._running = False
                except Exception:
                    pass

                time.sleep(0.1)

        finally:
            try:
                curses.nocbreak()
                self._stdscr.keypad(False)
                curses.echo()
                curses.endwin()
            except Exception:
                pass
