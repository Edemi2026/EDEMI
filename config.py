# =============================================================================
# config.py — EDEMI Smart Glasses
# Central configuration — change RUNNING_ON_PI to deploy to Pi
# =============================================================================

from pathlib import Path

# =============================================================================
# DEPLOYMENT FLAG — ONLY LINE YOU CHANGE BETWEEN PC AND PI
# =============================================================================
RUNNING_ON_PI = True   # False = PC testing | True = Pi deployment

# =============================================================================
# SYSTEM IDENTITY
# =============================================================================
DEVICE_NAME         = "EDEMI"
DEVICE_FULL_NAME    = "Enhanced Deaf Expression and Mobility Intelligence"
DEVICE_VERSION      = "v1.0"

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR            = Path(__file__).resolve().parent
MODEL_PATH          = BASE_DIR / "vosk-model-small-en-us-0.15"

# =============================================================================
# PLATFORM SPECIFIC — audio and environment thresholds
# Tuned separately for PC mic and Pi INMP441
# =============================================================================
if RUNNING_ON_PI:
    AUDIO_BLOCK_SIZE        = 800     # INMP441 optimal chunk size
    VOSK_SILENCE_THRESHOLD  = 0.0   # INMP441 is directional — filter silence
    ENV_THRESHOLD_DANGER    = 0.08   # 90+ dB — clap, bang, alarm siren
    ENV_THRESHOLD_HIGH      = 0.045  # 75-90 dB — vehicle, loud machinery
    ENV_THRESHOLD_MEDIUM    = 0.020  # 65-75 dB — raised voices, crowd noise
    ENV_THRESHOLD_LOW       = 0.010  # 55-65 dB — conversation nearby
else:
    AUDIO_BLOCK_SIZE        = 2000    # PC mic needs larger chunks
    VOSK_SILENCE_THRESHOLD  = 0.0     # No threshold — let Vosk decide naturally


# =============================================================================
# AR DISPLAY — Sony ECX336CN HDMI — deaf person sees this
# =============================================================================
AR_DISPLAY_WIDTH    = 640
AR_DISPLAY_HEIGHT   = 480
AR_DISPLAY_FPS      = 30

# Colors (RGB)
AR_BG_COLOR         = (10,  18,  30)
AR_TEXT_COLOR       = (255, 255, 255)
AR_SUGGESTION_COLOR = (180, 190, 200)
AR_SELECTED_COLOR   = (0,   255, 170)
AR_HEADER_COLOR     = (0,   255, 170)
AR_TIME_COLOR       = (120, 140, 160)
AR_ALERT_DANGER     = (255, 60,  60)
AR_ALERT_CAUTION    = (255, 200, 0)
AR_ALERT_INFO       = (200, 200, 200)

# Font sizes
AR_FONT_SPEECH      = 28
AR_FONT_SUGGESTION  = 22
AR_FONT_HEADER      = 14
AR_FONT_TIME        = 13
AR_FONT_ALERT       = 16
AR_FONT_STATUS      = 18

# Layout zones (y pixel positions)
AR_ZONE_TIME        = 10
AR_ZONE_ALERT       = 10
AR_ZONE_SPEECH      = 80
AR_ZONE_SUGGESTIONS = 260

# Suggestions
MAX_SUGGESTIONS     = 3

# =============================================================================
# TFT DISPLAY — ST7735 1.8" SPI — hearing person reads this
# =============================================================================
TFT_WIDTH           = 160
TFT_HEIGHT          = 128

# SPI GPIO pins (BCM) — Pi Zero 2W
TFT_DC_PIN          = 24
TFT_RST_PIN         = 25
TFT_CS_PIN          = 0
TFT_BL_PIN          = 13
TFT_SPI_PORT        = 0
TFT_SPI_DEVICE      = 0
TFT_SPI_SPEED       = 4000000

# Colors (RGB)
TFT_BG_COLOR        = (0,   0,   0)
TFT_TEXT_COLOR      = (255, 255, 255)
TFT_HEADER_BG       = (0,   51,  102)
TFT_HEADER_COLOR    = (0,   255, 170)
TFT_PROGRESS_COLOR  = (0,   255, 170)

# Timing
TFT_CLEAR_DELAY     = 10000     # ms — overridden by settings.json
TFT_ANIMATE_SPEED   = 25        # ms per letter

# =============================================================================
# MICROPHONE — INMP441 I2S
# =============================================================================
AUDIO_SAMPLE_RATE   = 16000
AUDIO_CHANNELS      = 1
AUDIO_DTYPE         = "int16"

# I2S GPIO pins — Pi Zero 2W
I2S_BCK_PIN         = 18
I2S_WS_PIN          = 19
I2S_DATA_PIN        = 20

# PC mic device (None = system default)
PC_MIC_DEVICE       = None

# =============================================================================
# CAPACITIVE TOUCH — HE-017 MPR121 I2C — temple mounted
# =============================================================================
TOUCH_I2C_BUS       = 1
TOUCH_I2C_ADDRESS   = 0x5A
TOUCH_IRQ_PIN       = 17
TOUCH_DEBOUNCE_MS   = 500

# Pad functions
TOUCH_PAD_UP        = 1
TOUCH_PAD_DOWN      = 2
TOUCH_PAD_SELECT    = 3
TOUCH_PAD_CLEAR_TFT = 4
TOUCH_PAD_CLEAR_SPK = 5
TOUCH_PAD_REPEAT    = 6

# PC keyboard simulation
KEY_UP              = "up"
KEY_DOWN            = "down"
KEY_SELECT          = "return"
KEY_CLEAR_TFT       = "c"
KEY_CLEAR_SPEECH    = "x"
KEY_REPEAT          = "r"

# =============================================================================
# ENVIRONMENT MONITOR
# =============================================================================
ENV_SPIKE_WINDOW        = 0.1
ENV_RHYTHM_WINDOW       = 2.0
ENV_SUSTAINED_WINDOW    = 1.5
ENV_ALERT_DURATION      = 5000   # ms
ENV_BLINK_SPEED_FAST    = 200    # ms
ENV_BLINK_SPEED_SLOW    = 600    # ms

ENV_ALERTS = {
    "danger":       "LOUD SOUND NEARBY",
    "vehicle":      "VEHICLE DETECTED",
    "conversation": "PEOPLE TALKING NEARBY",
    "knocking":     "KNOCK AT DOOR",
    "alarm":        "ALARM DETECTED",
}

# =============================================================================
# SPEECH ENGINE
# =============================================================================
SPEECH_PARTIAL_WORDS    = True
SPEECH_FLUSH_WINDOW     = 0.8
SPEECH_MIN_WORDS        = 1
SPEECH_SUGGESTION_DELAY = 1.2

# =============================================================================
# WEB CONFIG SERVER
# =============================================================================
WEB_HOST            = "0.0.0.0"
WEB_PORT            = 5000

# =============================================================================
# OPENAI — disabled, enable later with API key
# =============================================================================
USE_OPENAI          = False
OPENAI_MODEL        = "gpt-3.5-turbo"
OPENAI_MAX_TOKENS   = 120
OPENAI_TEMPERATURE  = 0.7
OPENAI_THROTTLE     = 2.0

# =============================================================================
# SYSTEM
# =============================================================================
BOOT_MESSAGE_AR     = "Hello, I am EDEMI\nStarting up..."
BOOT_MESSAGE_TFT    = "EDEMI STARTING"
READY_MESSAGE_AR    = "Listening..."
READY_MESSAGE_TFT   = "EDEMI READY"
BOOT_DELAY          = 3.0

THREAD_JOIN_TIMEOUT = 1.0
MAX_HISTORY         = 50
