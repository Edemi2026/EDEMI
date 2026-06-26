# =============================================================================
# system_monitor.py — EDEMI Smart Glasses
# Monitors system status: WiFi, uptime, power
# Updates AR display status bar continuously
# =============================================================================

import time
import threading
import subprocess
from config import RUNNING_ON_PI


def get_wifi_status():
    """
    Check WiFi/hotspot status.
    Returns: 'Hotspot' / 'WiFi' / 'No Network'
    """
    if not RUNNING_ON_PI:
        return "Simulated"

    try:
        # Check if hotspot is active
        result = subprocess.run(
            ["iwconfig", "wlan0"],
            capture_output=True, text=True, timeout=2
        )
        output = result.stdout.lower()

        if "mode:master" in output:
            return "Hotspot"
        elif "essid" in output and "off/any" not in output:
            return "WiFi"
        else:
            return "No Network"
    except Exception:
        return "Network"


def get_uptime():
    """
    Get system uptime as formatted string HH:MM:SS
    """
    if not RUNNING_ON_PI:
        return "00:00:00"

    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
        hours   = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception:
        return "00:00:00"


def get_power_status():
    """
    Returns power status string.
    Pi cannot read power bank level — shows Powered.
    """
    return "Powered"


def start_system_monitor(status_callback, stop_event=None):
    """
    Main system monitor loop.
    Calls status_callback every 30 seconds with updated status dict.

    Parameters:
        status_callback — called with status dict
        stop_event      — threading.Event to stop monitor
    """
    while not (stop_event and stop_event.is_set()):
        try:
            status = {
                "wifi":   get_wifi_status(),
                "uptime": get_uptime(),
                "power":  get_power_status(),
            }
            status_callback(status)
        except Exception as e:
            open("/tmp/edemi.log", "a").write(f"System monitor error: {e}\n")

        # Update every 30 seconds
        for _ in range(300):
            if stop_event and stop_event.is_set():
                return
            time.sleep(0.1)
