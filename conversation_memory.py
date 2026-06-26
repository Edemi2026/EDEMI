# =============================================================================
# conversation_memory.py — EDEMI Smart Glasses
# Tracks conversation history and manages context
# =============================================================================

import time
from settings_manager import get_setting
from config import MAX_HISTORY

class ConversationMemory:

    def __init__(self):
        self.history        = []   # Full conversation history
        self.last_input     = ""   # Last transcribed sentence
        self.last_reply     = ""   # Last reply sent
        self.session_start  = time.time()
        self.exchange_count = 0    # Number of completed exchanges

    def add_user_input(self, text):
        """Add transcribed speech to history."""
        if not text:
            return
        if not self.history or self.history[-1] != text:
            self.history.append(text)
            self.last_input = text
            if len(self.history) > MAX_HISTORY:
                self.history.pop(0)

    def add_reply(self, reply_text):
        """Record a sent reply."""
        self.last_reply  = reply_text
        self.exchange_count += 1

    def get_recent(self, n=5):
        """Get last n conversation turns."""
        return self.history[-n:] if self.history else []

    def clear(self):
        """Clear conversation history — new conversation."""
        self.history        = []
        self.last_input     = ""
        self.last_reply     = ""
        self.exchange_count = 0

    def get_session_duration(self):
        """Get session duration in seconds."""
        return int(time.time() - self.session_start)

    def is_repeat(self, text):
        """Check if this text was already said recently."""
        recent = self.get_recent(3)
        return any(text.lower() in h.lower() for h in recent)
