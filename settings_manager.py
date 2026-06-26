# =============================================================================
# settings_manager.py — EDEMI Smart Glasses
# Loads and saves runtime settings from settings.json
# All files import from here — single source of truth
# =============================================================================

import json
import threading
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent / "settings.json"

# Default settings — used if settings.json missing or key not found
DEFAULTS = {
    "user_name":            "",
    "user_religion":        "Christian",
    "user_reply_style":     "polite",
    "user_language":        "English",
    "user_gender":          "Male",
    "auto_reply":           True,
    "environment_alerts":   True,
    "mic_sensitivity":      "Medium",
    "tft_clear_delay":      10,
    "alert_duration":       5,
    "ar_text_size":         "Medium",
    "show_date":            True,
    "show_battery":         True,
    "show_wifi":            True,
    "emergency_message_1":  "I NEED HELP",
    "emergency_message_2":  "PLEASE CALL SOMEONE",
    "emergency_message_3":  "EMERGENCY — PLEASE HELP",
}

_settings = {}
_lock = threading.Lock()


def load_settings():
    """Load settings from settings.json into memory."""
    global _settings
    with _lock:
        if SETTINGS_PATH.exists():
            try:
                with open(SETTINGS_PATH, "r") as f:
                    loaded = json.load(f)
                _settings = {**DEFAULTS, **loaded}
            except Exception as e:
                open("/tmp/edemi.log", "a").write(f"Settings load error: {e}\n")
                _settings = DEFAULTS.copy()
        else:
            _settings = DEFAULTS.copy()
            save_settings()


def save_settings():
    """Save current settings to settings.json."""
    with _lock:
        try:
            with open(SETTINGS_PATH, "w") as f:
                json.dump(_settings, f, indent=2)
        except Exception as e:
            open("/tmp/edemi.log", "a").write(f"Settings save error: {e}\n")


def get_setting(key, default=None):
    """Get a setting value by key."""
    if not _settings:
        load_settings()
    return _settings.get(key, default if default is not None
                         else DEFAULTS.get(key))


def update_setting(key, value):
    """Update a single setting and save."""
    global _settings
    if not _settings:
        load_settings()
    with _lock:
        _settings[key] = value
    save_settings()


def update_settings(new_settings):
    """Update multiple settings at once and save."""
    global _settings
    if not _settings:
        load_settings()
    with _lock:
        _settings.update(new_settings)
    save_settings()


def get_all_settings():
    """Return all settings as dict."""
    if not _settings:
        load_settings()
    with _lock:
        return _settings.copy()


# Load on import
load_settings()
