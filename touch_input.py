# =============================================================================
# touch_input.py — EDEMI Smart Glasses
# Capacitive touch input handler for MPR121 (HE-017) via I2C
# 6 electrodes on temple — handles navigation, selection, menu, shutdown
# =============================================================================

import time
import threading
from config import (
    RUNNING_ON_PI,
    TOUCH_I2C_BUS,
    TOUCH_I2C_ADDRESS,
    TOUCH_PAD_UP,
    TOUCH_PAD_DOWN,
    TOUCH_PAD_SELECT,
    TOUCH_PAD_CLEAR_TFT,
    TOUCH_PAD_CLEAR_SPK,
    TOUCH_PAD_REPEAT,
    TOUCH_DEBOUNCE_MS,
)

if RUNNING_ON_PI:
    import smbus2

MENU_HOLD_SECONDS      = 3.0
EMERGENCY_HOLD_SECONDS = 2.0
POLL_INTERVAL          = 0.05   # 50ms

# =============================================================================
# MPR121 READER (Pi only)
# =============================================================================

class MPR121Reader:
    """
    Reads touch state from MPR121 (HE-017) via I2C.
    Pure polling — no IRQ pin required.
    Electrodes 0-5 map to pads 1-6.
    """

    def __init__(self):
        self.bus     = smbus2.SMBus(TOUCH_I2C_BUS)
        self.address = TOUCH_I2C_ADDRESS
        self._init()

    def _init(self):
        """Full MPR121 initialization sequence."""
        # Guard — only init once
        try:
            ecr = self.bus.read_byte_data(self.address, 0x5E)
            if ecr & 0x3F:  # Already running
                return
        except Exception:
            pass
        # Soft reset
        self.bus.write_byte_data(self.address, 0x80, 0x63)
        time.sleep(0.01)

        # Baseline filter — rising
        self.bus.write_byte_data(self.address, 0x2B, 0x01)
        self.bus.write_byte_data(self.address, 0x2C, 0x01)
        self.bus.write_byte_data(self.address, 0x2D, 0x00)
        self.bus.write_byte_data(self.address, 0x2E, 0x00)
        # Baseline filter — falling
        self.bus.write_byte_data(self.address, 0x2F, 0x01)
        self.bus.write_byte_data(self.address, 0x30, 0x01)
        self.bus.write_byte_data(self.address, 0x31, 0xFF)
        self.bus.write_byte_data(self.address, 0x32, 0x02)

        # Touch/release thresholds for electrodes 0-5
        for i in range(6):
            self.bus.write_byte_data(self.address, 0x41 + i * 2, 12)  # touch
            self.bus.write_byte_data(self.address, 0x42 + i * 2, 6)   # release

        # Charge time config
        self.bus.write_byte_data(self.address, 0x5C, 0x10)
        self.bus.write_byte_data(self.address, 0x5D, 0x24)

        # ECR — run mode, enable 6 electrodes
        self.bus.write_byte_data(self.address, 0x5E, 0x86)
        time.sleep(0.05)

    def read_touch(self):
        """
        Read which pad is currently touched.
        Returns pad number (1-6) or 0 if none.
        Electrode N = pad N+1.
        """
        try:
            low  = self.bus.read_byte_data(self.address, 0x00)
            high = self.bus.read_byte_data(self.address, 0x01)
            raw  = low | (high << 8)

            for electrode in range(6):
                if raw & (1 << electrode):
                    return electrode + 1   # pad is 1-indexed
            return 0
        except Exception as e:
            open("/tmp/edemi.log", "a").write(f"Touch read error: {e}\n")
            return 0

    def cleanup(self):
        self.bus.close()


# =============================================================================
# TOUCH CONTROLLER — unchanged logic
# =============================================================================

class TouchController:
    """
    High level touch controller.
    Handles debouncing, hold detection, menu state, navigation.
    """

    def __init__(self, ui):
        self.ui              = ui
        self.last_touch_time = 0
        self.last_pad        = 0
        self.pad_press_time  = {}
        self.menu_open       = False
        self.menu_index      = 0
        self.menu_items      = ["Resume", "Clear Conversation", "Shutdown"]
        self._lock           = threading.Lock()

    def debounce_ok(self):
        now = time.time() * 1000
        if now - self.last_touch_time < TOUCH_DEBOUNCE_MS:
            return False
        self.last_touch_time = now
        return True

    def handle_pad(self, pad):
        if pad == 0 or not self.debounce_ok():
            return

        with self._lock:
            if pad not in self.pad_press_time:
                self.pad_press_time[pad] = time.time()

            if self.menu_open:
                self._handle_menu_pad(pad)
                return

            if pad == TOUCH_PAD_REPEAT:
                hold = time.time() - self.pad_press_time.get(pad, time.time())
                if hold >= MENU_HOLD_SECONDS:
                    self._open_menu()
                    return

            if pad == TOUCH_PAD_SELECT:
                hold = time.time() - self.pad_press_time.get(pad, time.time())
                if hold >= EMERGENCY_HOLD_SECONDS:
                    self._trigger_emergency()
                    return

            self._handle_normal_pad(pad)

    def handle_pad_release(self, pad):
        self.pad_press_time.pop(pad, None)

    def _handle_normal_pad(self, pad):
        if pad == TOUCH_PAD_UP:
            self.ui.scroll_suggestions("up")
        elif pad == TOUCH_PAD_DOWN:
            self.ui.scroll_suggestions("down")
        elif pad == TOUCH_PAD_SELECT:
            self.ui.confirm_selection()
        elif pad == TOUCH_PAD_CLEAR_TFT:
            self.ui.clear_tft()
        elif pad == TOUCH_PAD_CLEAR_SPK:
            self.ui.clear_speech()
        elif pad == TOUCH_PAD_REPEAT:
            self.ui.repeat_last_speech()

    def _handle_menu_pad(self, pad):
        if pad == TOUCH_PAD_UP:
            self.menu_index = max(0, self.menu_index - 1)
            self.ui.update_menu(self.menu_items, self.menu_index)
        elif pad == TOUCH_PAD_DOWN:
            self.menu_index = min(len(self.menu_items) - 1, self.menu_index + 1)
            self.ui.update_menu(self.menu_items, self.menu_index)
        elif pad == TOUCH_PAD_SELECT:
            self._execute_menu_item(self.menu_items[self.menu_index])
        elif pad == TOUCH_PAD_REPEAT:
            self._close_menu()

    def _open_menu(self):
        self.menu_open  = True
        self.menu_index = 0
        self.ui.show_menu(self.menu_items, self.menu_index)

    def _close_menu(self):
        self.menu_open = False
        self.ui.hide_menu()

    def _execute_menu_item(self, item):
        self._close_menu()
        if item == "Resume":
            pass
        elif item == "Clear Conversation":
            self.ui.clear_speech()
            self.ui.clear_tft()
        elif item == "Shutdown":
            self.ui.show_shutdown_screen()
            threading.Timer(2.0, self._do_shutdown).start()

    def _trigger_emergency(self):
        from response_engine import get_emergency_replies
        self.ui.show_emergency(get_emergency_replies())

    def _do_shutdown(self):
        import subprocess
        try:
            subprocess.run(["sudo", "shutdown", "-h", "now"])
        except Exception as e:
            open("/tmp/edemi.log", "a").write(f"Shutdown error: {e}\n")


# =============================================================================
# MAIN TOUCH LISTENER
# =============================================================================

def start_touch_listener(ui, stop_event=None):
    """
    Main touch input loop for Pi hardware.
    Pure I2C polling — no IRQ pin required.
    """
    controller = TouchController(ui)

    if RUNNING_ON_PI:
        reader = MPR121Reader()
        open("/tmp/edemi.log", "a").write("Touch input started (MPR121 polling)\n")

        try:
            while not (stop_event and stop_event.is_set()):
                pad = reader.read_touch()

                if pad > 0:
                    # Record press time
                    press_start = time.time()
                    controller.handle_pad(pad)

                    # Wait for release — check for hold
                    while reader.read_touch() == pad:
                        hold_duration = time.time() - press_start
                        if pad == TOUCH_PAD_REPEAT and hold_duration >= MENU_HOLD_SECONDS:
                            controller._open_menu()
                            # Wait for full release
                            while reader.read_touch() == pad:
                                time.sleep(0.02)
                            break
                        if pad == TOUCH_PAD_SELECT and hold_duration >= EMERGENCY_HOLD_SECONDS:
                            controller._trigger_emergency()
                            while reader.read_touch() == pad:
                                time.sleep(0.02)
                            break
                        time.sleep(0.02)
                    controller.handle_pad_release(pad)

                time.sleep(POLL_INTERVAL)
        finally:
            reader.cleanup()

    else:
        open("/tmp/edemi.log", "a").write("Touch input simulation\n")
        while not (stop_event and stop_event.is_set()):
            time.sleep(0.1)
