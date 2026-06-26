# =============================================================================
# environment_monitor.py — EDEMI Smart Glasses
# Simple reliable environment sound detection
# Based on original working code — kept simple and direct
# =============================================================================

import queue
import numpy as np
from config import (
    ENV_THRESHOLD_DANGER,
    ENV_THRESHOLD_HIGH,
    ENV_THRESHOLD_MEDIUM,
    ENV_THRESHOLD_LOW,
)

def interpret_energy(energy):
    """Classify sound energy into alert type and level."""

    if energy > ENV_THRESHOLD_DANGER:
        return {
            "message": "LOUD SOUND NEARBY",
            "level":   "danger",
            "type":    "danger"
        }

    if energy > ENV_THRESHOLD_HIGH:
        return {
            "message": "ALARM DETECTED",
            "level":   "danger",
            "type":    "alarm"
        }

    if energy > ENV_THRESHOLD_MEDIUM:
        return {
            "message": "VEHICLE DETECTED",
            "level":   "caution",
            "type":    "vehicle"
        }

    if energy > ENV_THRESHOLD_LOW:
        return {
            "message": "PEOPLE TALKING NEARBY",
            "level":   "info",
            "type":    "conversation"
        }

    return None


def start_environment_monitor(audio_queue, env_callback, stop_event=None):
    """
    Main environment monitor loop.
    Simple and direct — reads audio, measures energy, triggers alerts.
    """
    while not (stop_event and stop_event.is_set()):
        try:
            raw = audio_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if not raw:
            continue

        try:
            data   = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
            data   = data / 32768.0
            energy = float(np.sqrt(np.mean(data ** 2)))
        except Exception:
            continue

        alert = interpret_energy(energy)

        if alert:
            env_callback(alert)
