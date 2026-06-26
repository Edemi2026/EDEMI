
# ======.=======================================================================
# main.py — EDEMI Smart Glasses
# Entry point — run this file only: python3 main.py
# =============================================================================

import threading
import queue
import sys
import time
from pathlib import Path

from config import (
    RUNNING_ON_PI,
    MODEL_PATH,
    AUDIO_SAMPLE_RATE,
    AUDIO_CHANNELS,
    AUDIO_BLOCK_SIZE,
    AUDIO_DTYPE,
    PC_MIC_DEVICE,
    THREAD_JOIN_TIMEOUT,
    BOOT_MESSAGE_AR,
    BOOT_MESSAGE_TFT,
    READY_MESSAGE_AR,
    READY_MESSAGE_TFT,
    BOOT_DELAY,
    WEB_HOST,
    WEB_PORT,
    DEVICE_NAME,
    DEVICE_VERSION,
)
from settings_manager import load_settings

# =============================================================================
# AUDIO QUEUES AND EVENTS
# Two separate queues — speech engine and env monitor never share
# =============================================================================
speech_queue = queue.Queue()
env_queue    = queue.Queue()
stop_event   = threading.Event()

# =============================================================================
# AUDIO CALLBACK — PC sounddevice
# =============================================================================
def audio_callback(indata, frames, time_info, status):
    if status:
        print(f"Audio status: {status}")
        return
    data = bytes(indata)
    speech_queue.put(data)
    env_queue.put(data)

# =============================================================================
# I2S AUDIO CAPTURE — Pi INMP441
# =============================================================================

def start_i2s_capture():
    import alsaaudio
    import struct

    inp = alsaaudio.PCM(
        alsaaudio.PCM_CAPTURE,
        alsaaudio.PCM_NORMAL,
        channels=2,
        rate=16000,
        format=alsaaudio.PCM_FORMAT_S16_LE,
        periodsize=1600,
        device='plughw:0,0'
    )
    print("Microphone started (plughw S16_LE)")

    while not stop_event.is_set():
        length, data = inp.read()
        if length < 0:
            continue
        if length > 0 and data:
            unpacked = struct.unpack(f"<{len(data)//2}h", data)
            left_channel = unpacked[0::2]
            mono_processed = bytearray(len(data) // 2)
            struct.pack_into(
                f"<{len(left_channel)}h",
                mono_processed,
                0,
                *[max(-32768, min(32767, sample * 6))
                  for sample in left_channel]
            )
            speech_queue.put(bytes(mono_processed))
            env_queue.put(bytes(mono_processed))



# ============================================================================
# LOAD VOSK MODEL
# ============================================================================
def load_vosk_model():
    import vosk
    if not MODEL_PATH.exists():
        print(f"ERROR: Vosk model not found at {MODEL_PATH}")
        print("Please download vosk-model-small-en-us-0.15")
        sys.exit(1)
    try:
        print(f"Loading Vosk model...")
        model = vosk.Model(str(MODEL_PATH))
        print("Vosk model loaded successfully")
        return model
    except Exception as e:
        print(f"ERROR loading Vosk model: {e}")
        sys.exit(1)

# =============================================================================
# MAIN
# =============================================================================
def main():
    print("=" * 52)
    print(f"  {DEVICE_NAME} {DEVICE_VERSION} — Smart Glasses for the Deaf")
    print(f"  Mode: {'Raspberry Pi' if RUNNING_ON_PI else 'PC Simulation'}")
    print("=" * 52)

    # Load settings first
    load_settings()
    print("Settings loaded")

    # Load Vosk model
    model = load_vosk_model()

    # Import modules
    from conversation_memory import ConversationMemory
    from speech_engine       import start_speech_engine
    from environment_monitor import start_environment_monitor
    from system_monitor      import start_system_monitor
    from web_config          import start_web_server

    if RUNNING_ON_PI:
        from ar_display_pi  import ARDisplay
        from oled_display_pi import TFTDisplay
        from touch_input    import start_touch_listener
    else:
        from ar_display  import ARDisplay
        from tft_display import TFTDisplay

    # Initialize
    memory = ConversationMemory()
    print("Initializing displays...")

    tft = TFTDisplay()
    ui  = ARDisplay(tft)

    # Boot screen
    ui.show_status(BOOT_MESSAGE_AR)
    tft.show_message(BOOT_MESSAGE_TFT)
    print(f"Boot screen shown — waiting {BOOT_DELAY}s...")
    time.sleep(BOOT_DELAY)

    # -------------------------------------------------------------------------
    # THREAD DEFINITIONS
    # -------------------------------------------------------------------------

    # Audio capture
    if RUNNING_ON_PI:
        audio_thread = threading.Thread(
             target=start_i2s_capture,
             daemon=True, name="AudioCapture")
        stream = None
    else:
        import sounddevice as sd
        stream = sd.RawInputStream(
            samplerate = AUDIO_SAMPLE_RATE,
            blocksize  = AUDIO_BLOCK_SIZE,
            dtype      = AUDIO_DTYPE,
            channels   = AUDIO_CHANNELS,
            device     = PC_MIC_DEVICE,
            callback   = audio_callback
        )
        audio_thread = None
    # Speech engine
    speech_thread = threading.Thread(
        target = start_speech_engine,
        args   = (model, speech_queue,
                  ui.update_speech,
                  ui.show_suggestions,
                  memory, stop_event),
        daemon = True, name = "SpeechEngine"
    )

    # Environment monitor
    env_thread = threading.Thread(
        target = start_environment_monitor,
        args   = (env_queue, ui.update_environment, stop_event),
        daemon = True, name = "EnvMonitor"
    )

    # System monitor
    sys_thread = threading.Thread(
        target = start_system_monitor,
        args   = (ui.update_system_status, stop_event),
        daemon = True, name = "SysMonitor"
    )

    # Web config server
    web_thread = threading.Thread(
        target = start_web_server,
        args   = (WEB_HOST, WEB_PORT),
        daemon = True, name = "WebConfig"
    )

    # Touch input (Pi only)
    if RUNNING_ON_PI:
        touch_thread = threading.Thread(
            target = start_touch_listener,
            args   = (ui, stop_event),
            daemon = True, name = "TouchInput"
        )
    else:
        touch_thread = None

    # -------------------------------------------------------------------------
    # LAUNCH
    # -------------------------------------------------------------------------
    try:
        speech_thread.start()
        print("Speech engine started")

        env_thread.start()
        print("Environment monitor started")

        sys_thread.start()
        print("System monitor started")

        web_thread.start()
        print(f"Web config started — http://192.168.4.1:{WEB_PORT}")

        if touch_thread:
            touch_thread.start()
            print("Touch input started")

        if audio_thread:
            audio_thread.start()
            print("I2S audio capture started")

        if stream:
            stream.start()
            print("PC microphone started")

        # Ready
        ui.show_status(READY_MESSAGE_AR)
        tft.show_message(READY_MESSAGE_TFT)
        time.sleep(0.5)

        print("-" * 52)
        print("EDEMI is ready. Listening...")
        print("-" * 52)

        # Run UI — blocks until closed
        ui.run()

    except KeyboardInterrupt:
        print("\nShutting down EDEMI...")

    finally:
        stop_event.set()

        if stream:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass

        for t in [speech_thread, env_thread, sys_thread,
                  touch_thread, audio_thread]:
            if t and t.is_alive():
                t.join(timeout=THREAD_JOIN_TIMEOUT)

        print("EDEMI shutdown complete.")

# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    main()
