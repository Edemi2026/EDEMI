# =============================================================================
# speech_engine.py — EDEMI Smart Glasses
# Core speech recognition and conversation intelligence engine
# Handles: real time transcription, turn taking detection,
#          intent awareness, auto reply timing, speech clearing
# =============================================================================
import os
os.environ["OMP_NUM_THREADS"] = "1"
import queue
import json
import time
import threading
import numpy as np
import vosk
vosk.SetLogLevel(-1)

from response_engine import process_speech, get_emergency_replies, detect_intent
from settings_manager import get_setting
from config import (
    RUNNING_ON_PI,
    SPEECH_PARTIAL_WORDS,
    SPEECH_FLUSH_WINDOW,
    SPEECH_MIN_WORDS,
    SPEECH_SUGGESTION_DELAY,
    AUDIO_SAMPLE_RATE,
    VOSK_SILENCE_THRESHOLD,
)

# =============================================================================
# TEXT CLEANING
# =============================================================================

def clean_text(text):
    words = text.split()
    filtered = []
    for w in words:
        if not filtered or w != filtered[-1]:
            filtered.append(w)
    sentence = " ".join(filtered).strip()
    if len(sentence) > 2:
        sentence = sentence[0].upper() + sentence[1:]
        if not sentence.endswith(("?", ".", "!")):
            sentence += "."
    return sentence


def is_valid_sentence(text):
    words = text.lower().split()
    if len(words) < SPEECH_MIN_WORDS:
        return False
    if text.lower() in ["the", "a", "an", "the."]:
        return False
    if len(set(words)) == 1 and len(words) > 1:
        return False
    fillers = {"um", "uh", "hmm", "err"}
    if all(w.strip(".,?!") in fillers for w in words):
        return False
    return True


# =============================================================================
# TURN TAKING DETECTOR
# =============================================================================

class TurnTakingDetector:

    STORY_WORDS = [
        "and then", "so then", "after that", "but then",
        "and also", "anyway", "so basically", "you see",
        "the thing is", "let me tell you", "as i was saying",
        "furthermore", "moreover", "additionally"
    ]

    YIELD_SIGNALS = [
        "right?", "isn't it", "don't you think",
        "wouldn't you say", "don't you agree",
        "yes?", "no?", "okay?", "correct?"
    ]

    URGENT_PATTERNS = [
        "are you okay", "watch out", "careful",
        "danger", "emergency", "urgent",
        "fire", "police", "ambulance", "are you alright"
    ]

    def __init__(self):
        self.last_speech_time = time.time()
        self.story_mode = False
        self.last_intent = None

    def update(self, text, intent):
        self.last_speech_time = time.time()
        self.last_intent = intent
        text_lower = text.lower()
        if any(sw in text_lower for sw in self.STORY_WORDS):
            self.story_mode = True
        elif text.strip().endswith("?"):
            self.story_mode = False
        elif intent in ["greeting", "farewell", "question"]:
            self.story_mode = False

    def should_reply_now(self, text, intent):
        text_lower = text.lower()
        if any(u in text_lower for u in self.URGENT_PATTERNS):
            return "urgent"
        if intent in ["greeting", "farewell", "thanks",
                      "apology", "how_are_you", "name_called",
                      "deaf_explain", "identity", "repeat_request",
                      "agreement", "disagreement", "compliment",
                      "waiting", "ghanaian_surprise"]:
            return "now"
        if intent in ["incomplete", "thinking"]:
            return "wait"
        if self.story_mode and intent in ["story", "statement",
                                           "emotional_statement"]:
            return "ack"
        if any(ys in text_lower for ys in self.YIELD_SIGNALS):
            return "now"
        if intent == "question" and text.strip().endswith("?"):
            return "now"
        if intent == "instruction":
            return "now"
        if intent in ["statement", "emotional_statement"]:
            return "ack"
        return "wait"


# =============================================================================
# AUTO REPLY TIMER
# =============================================================================

class AutoReplyTimer:

    def __init__(self):
        self._timer = None
        self._lock = threading.Lock()

    def schedule(self, delay, callback, reply_text):
        with self._lock:
            self._cancel_existing()
            self._timer = threading.Timer(delay, callback, args=[reply_text])
            self._timer.daemon = True
            self._timer.start()

    def cancel(self):
        with self._lock:
            self._cancel_existing()

    def _cancel_existing(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None


# =============================================================================
# MAIN SPEECH ENGINE
# =============================================================================

def start_speech_engine(
    model,
    audio_queue,
    speech_callback,
    reply_callback,
    memory,
    stop_event=None
):
    recognizer = vosk.KaldiRecognizer(model, AUDIO_SAMPLE_RATE)
    recognizer.SetWords(True)
    recognizer.SetPartialWords(True)

    detector = TurnTakingDetector()
    auto_timer = AutoReplyTimer()

    committed_text       = ""
    last_partial         = ""
    last_processed_text  = ""
    last_suggestion_time = time.time() - 2.0
    last_commit_time     = time.time()
    force_timer_active   = False

    def send_reply(reply_dict):
        if reply_dict and reply_dict.get("reply_type") != "none":
            reply_callback(reply_dict)

    def schedule_auto_reply(result, text):
        delay      = result.get("delay", 1.5)
        reply_type = result.get("reply_type")
        content    = result.get("content")

        if not get_setting("auto_reply", True):
            if isinstance(content, str):
                reply_callback({
                    "reply_type": "prompted",
                    "content": [content],
                    "intent": result.get("intent")
                })
            return

        def do_send(reply_text):
            reply_callback({
                "reply_type": reply_type,
                "content": reply_text,
                "intent": result.get("intent")
            })

        # Notify AR of pending auto reply so user can cancel
        reply_callback({
            "reply_type": "auto_pending",
            "content": content,
            "intent": result.get("intent"),
            "delay": delay
        })
        auto_timer.schedule(delay, do_send, content)

    def force_suggestions(text):
        nonlocal last_processed_text, committed_text
        if text and text != last_processed_text:
            cleaned = clean_text(text)
            result = process_speech(cleaned, memory.history)
            last_processed_text = cleaned
            committed_text = ""
            if result["reply_type"] == "none":
                result = {
                    "reply_type": "prompted",
                    "content": [
                        "I understand, please",
                        "Could you repeat that?",
                        "Please go ahead"
                    ],
                    "intent": "forced"
                }
            send_reply(result)

    # -------------------------------------------------------------------------
    # MAIN LOOP
    # -------------------------------------------------------------------------
    while True:
        if stop_event and stop_event.is_set():
            break

        try:
# Drain stale chunks to stay real-time
            while audio_queue.qsize() > 3:
                try:
                    audio_queue.get_nowait()
                except:
                    break

            data = audio_queue.get(timeout=1.0)

        except queue.Empty:
            now = time.time()
            if (committed_text
                    and not last_partial
                    and not force_timer_active
                    and now - last_commit_time >= 3.0
                    and committed_text != last_processed_text):
                force_timer_active = True
                t = threading.Thread(
                    target=force_suggestions,
                    args=(committed_text,),
                    daemon=True
                )
                t.start()
            continue

        if not data:
            continue
        #if RUNNING_ON_PI:
        #    audio = np.frombuffer(data, dtype=np.int16)
        #    mono  = audio[0::2].astype(np.int16)
         #   data  = mono.tobytes()
        # Platform aware silence filtering
        # On Pi — filter silence from INMP441
        # On PC — let Vosk decide naturally
        if False:
            data_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            energy  = float(np.sqrt(np.mean(data_np ** 2)))
            if energy < VOSK_SILENCE_THRESHOLD:
                continue
#        print(f"Audio chunk: {len(data)}")
        if recognizer.AcceptWaveform(data):
            # FINAL RESULT
            result = json.loads(recognizer.Result())
            text = result.get("text", "").strip()

            if text:
                committed_text += (" " + text) if committed_text else text
                cleaned = clean_text(committed_text)
                speech_callback(cleaned)
                detector.update(cleaned, "")

                open("/tmp/vosk_log.txt", "a").write(cleaned + "\n")
                if is_valid_sentence(cleaned) and cleaned != last_processed_text:
                    last_processed_text = cleaned
                    memory.add_user_input(cleaned)
                    reply_result = process_speech(cleaned, memory.history)
                    reply_type   = reply_result.get("reply_type")

                    if reply_type == "emergency":
                        send_reply(reply_result)
                    elif reply_type in ["auto_social", "auto_name"]:
                        # Single word intents reply instantly — no timer risk
                        if len(cleaned.split()) <= 2:
                            send_reply(reply_result)
                        else:
                            schedule_auto_reply(reply_result, cleaned)
                    elif reply_type in ["auto_ack", "auto_ambiguous", "auto_unclear"]:
                        schedule_auto_reply(reply_result, cleaned)
                    elif reply_type == "prompted":
                        send_reply(reply_result)

                    force_timer_active = False

            last_partial     = ""
            last_commit_time = time.time()

        else:
            # PARTIAL RESULT
            try:
                partial = json.loads(recognizer.PartialResult())
            except json.JSONDecodeError:
                partial = {}

            raw = partial.get("partial_result", "") or partial.get("partial", "")
            if isinstance(raw, list):
                partial_text = " ".join(w.get("word", "") for w in raw).strip()
            else:
                partial_text = str(raw).strip()

            if partial_text != last_partial:
                display = (committed_text + " " + partial_text).strip() \
                          if committed_text else partial_text
                speech_callback(display)

                now = time.time()
                if (len(partial_text.split()) >= 3
                        and partial_text != last_processed_text
                        and now - last_suggestion_time > SPEECH_SUGGESTION_DELAY):

                    last_suggestion_time = now
                    partial_intent = detect_intent(partial_text)

                    if partial_intent in ["question", "instruction",
                                          "concern", "urgent"]:
                        cleaned_partial = clean_text(partial_text)
                        partial_result  = process_speech(
                            cleaned_partial, memory.history)
                        if partial_result["reply_type"] == "prompted":
                            send_reply(partial_result)

                last_partial       = partial_text
                force_timer_active = False

        # FLUSH WINDOW
        now = time.time()
        if now - last_commit_time >= SPEECH_FLUSH_WINDOW:
            if committed_text and not last_partial:
                final = clean_text(committed_text)
                if is_valid_sentence(final) and final != last_processed_text:
                    last_processed_text = final
                    memory.add_user_input(final)
                    reply_result = process_speech(final, memory.history)
                    send_reply(reply_result)
                committed_text     = ""
                force_timer_active = False
            last_commit_time = now
