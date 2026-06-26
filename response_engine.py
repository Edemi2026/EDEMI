# =============================================================================
# response_engine.py — EDEMI Smart Glasses
# Complete reply generation system v2.0
# Ghana-aware | Religion-aware | 20 intent clusters
# =============================================================================

import datetime
import random
from settings_manager import get_setting

# =============================================================================
# INTENT TRIGGER BANKS
# =============================================================================

GREETING_WORDS = [
    "good morning", "good afternoon", "good evening", "good night",
    "hello", "hi", "hey", "howdy", "greetings", "good day",
    "what's up", "whats up", "how do you do",
    "pleased to meet you", "nice to meet you", "great to meet you",
    # Ghanaian
    "akwaaba", "how now", "how far", "charley", "chale",
    "you dey", "medaase"
]

FAREWELL_WORDS = [
    "goodbye", "good bye", "bye bye", "bye", "farewell",
    "see you later", "see you soon", "see you tomorrow",
    "until next time", "so long", "take care",
    "have a good day", "have a nice day", "have a great day",
    "have a good night", "have a good evening",
    # Ghanaian
    "make we go", "i dey go", "later charley", "i go come", "safe"
]

CONCERN_WORDS = [
    "are you okay", "are you alright", "you okay", "you alright",
    "everything okay", "are you fine", "what happened",
    "are you hurt", "you doing okay", "is everything fine",
    # Ghanaian
    "you dey okay", "you dey fine", "everything dey okay", "how you dey"
]

URGENT_WORDS = [
    "danger", "emergency",
    "fire", "police", "ambulance", "call an ambulance",
    "call the police", "call for help"
]

HOW_ARE_YOU_PHRASES = [
    "how are you", "how are you doing", "how do you do",
    "how have you been", "how are things", "how is everything",
    "how is life", "how are you feeling", "you good",
    # Ghanaian
    "how now", "how far", "you dey", "how you dey"
]

GRATITUDE_WORDS = [
    "thank you", "thanks", "thank you so much", "many thanks",
    "i appreciate", "i appreciate it", "appreciate that",
    "that was kind", "that is kind", "you are kind",
    "medaase"
]

APOLOGY_WORDS = [
    "sorry", "i apologize", "i am sorry", "my apologies",
    "excuse me", "pardon", "forgive me", "my bad",
    "i beg your pardon"
]

DEAF_TRIGGER_PHRASES = [
    "are you deaf", "can you hear", "why aren't you talking",
    "why are you not talking", "why don't you speak",
    "why are you not speaking", "can't you talk", "cannot you talk",
    "are you mute", "you can't hear", "you cannot hear",
    "do you have hearing", "hearing problem", "hearing loss",
    "what is that on your face", "what are those glasses",
    "what is that device", "what are you wearing",
    "why are you not responding", "why aren't you responding"
]

IDENTITY_PHRASES = [
    "what is your name", "what's your name", "who are you",
    "tell me your name", "may i know your name", "your name please",
    "what do they call you", "what should i call you"
]

REPEAT_PHRASES = [
    "say again", "repeat that", "repeat please", "say that again",
    "come again", "what did you say", "i didn't catch that",
    "i did not catch that", "could you repeat", "one more time",
    "what was that", "didn't hear you", "did not hear you",
    "can you say that again", "please repeat"
]

AGREEMENT_PHRASES = [
    "i agree", "you are right", "that is correct", "exactly",
    "absolutely", "definitely", "of course", "certainly",
    "that is true", "i think so too", "me too", "same here",
    "that makes sense", "totally", "indeed",
    # Ghanaian
    "ebi true", "straight", "no be lie", "for real", "that one correct"
]

DISAGREEMENT_PHRASES = [
    "i disagree", "i don't think so", "i do not think so",
    "that is wrong", "not really", "i am not sure about that",
    "i doubt it", "that is not right", "i beg to differ",
    "actually no", "not exactly"
]

COMPLIMENT_PHRASES = [
    "you look good", "you look great", "you look nice",
    "well done", "good job", "great job", "nicely done",
    "you did well", "i like your", "that looks nice",
    "that is beautiful", "you are smart", "you are brilliant",
    "impressive", "amazing work", "excellent", "you are talented"
]

LOCATION_PHRASES = [
    "where is", "how do i get to", "how do i find",
    "where can i find", "directions to", "nearest",
    "how far is", "is there a", "where are you from",
    "which way", "where do i go", "can you direct"
]

PAYMENT_PHRASES = [
    "how much", "what is the price", "what does it cost",
    "do you have change", "cash or card", "mobile money",
    "momo", "do you accept", "is it expensive", "the cost",
    "how much is it", "what is the cost", "pay here"
]

WAITING_PHRASES = [
    "one moment", "hold on", "just a second", "wait please",
    "give me a minute", "bear with me", "hold please",
    "just a moment", "i will be right back", "wait for me"
]

PERMISSION_PHRASES = [
    "can i", "may i", "is it okay", "do you mind",
    "would you mind", "is it alright", "am i allowed",
    "is that okay", "can we", "shall we", "are we allowed"
]

INVITATION_PHRASES = [
    "would you like to", "do you want to", "come join",
    "join us", "come with us", "want to come",
    "are you coming", "will you come", "dinner", "lunch",
    "party", "event", "gathering", "meeting", "visit"
]

OPINION_PHRASES = [
    "what do you think", "your opinion", "do you agree",
    "do you like", "what is your view", "how do you feel about",
    "what do you say", "do you believe", "in your opinion"
]

HELP_PHRASES = [
    "can i help", "do you need help", "need assistance",
    "can i assist", "let me help", "do you want help",
    "should i help", "can we help", "may i assist"
]

FOOD_PHRASES = [
    "eat", "food", "hungry", "drink", "thirsty",
    "water", "tea", "coffee", "snack", "meal",
    "something to eat", "something to drink", "are you hungry"
]

EMOTIONAL_WORDS_POSITIVE = [
    "amazing", "wonderful", "great", "fantastic", "beautiful",
    "happy", "excited", "blessed", "grateful", "excellent",
    "brilliant", "outstanding", "superb", "incredible"
]

EMOTIONAL_WORDS_NEGATIVE = [
    "terrible", "awful", "horrible", "sad", "angry",
    "upset", "problem", "difficult", "hard", "struggling",
    "depressed", "stressed", "worried", "scared", "afraid"
]

GHANAIAN_SURPRISE = [
    "ei", "eii", "herh", "ebei", "oh charley",
    "waa", "ah", "chai"
]

QUESTION_STARTERS = [
    "what", "how", "when", "where", "who", "why",
    "would", "could", "should", "do you", "are you",
    "can you", "will you", "have you", "did you",
    "is it", "is there", "was it", "were you"
]

STORY_CONNECTORS = [
    "and then", "so then", "after that", "but then",
    "and also", "furthermore", "anyway", "so basically",
    "you see", "the thing is", "let me tell you",
    "as i was saying"
]

INCOMPLETE_ENDINGS = [
    "and", "but", "or", "so", "that", "because",
    "when", "if", "the", "a", "an", "to", "for",
    "with", "about", "from", "into", "then"
]

THINKING_FILLERS = [
    "um", "uh", "hmm", "err", "like", "you know",
    "i mean", "sort of", "kind of", "basically"
]

INSTRUCTION_WORDS = [
    "please", "come", "go", "bring", "take", "help",
    "stop", "wait", "look", "listen", "follow",
    "sit", "stand", "move", "hold"
]

# =============================================================================
# REPLY BANKS
# =============================================================================

AUTO_SOCIAL_REPLIES = {
    "good morning":     "Please, good morning!",
    "good afternoon":   "Please, good afternoon!",
    "good evening":     "Please, good evening!",
    "good night":       "Please, good night! Rest well.",
    "hello":            "Please, hello! How can I help?",
    "hi":               "Please, hi there!",
    "hey":              "Please, hey there!",
    "howdy":            "Please, hello there!",
    "greetings":        "Please, greetings!",
    "good day":         "Please, good day!",
    "good after noon":  "Please, good afternoon!",
    "good eve ning":    "Please, good evening!",
    "what's up":        "Please, all is well!",
    "whats up":         "Please, all is well!",
    "akwaaba":          "Please, akwaaba! You are welcome!",
    "how now":          "Please, all is well! How are you?",
    "how far":          "Please, I am fine! And you?",
    "charley":          "Please, yes! How can I help?",
    "chale":            "Please, yes! How can I help?",
    "you dey":          "Please, I dey! How are you?",
    "goodbye":          "Goodbye! Please take care.",
    "good bye":         "Goodbye! Please take care.",
    "bye":              "Bye! Please take care.",
    "see you":          "See you! Please take care.",
    "farewell":         "Farewell! Please take care.",
    "take care":        "Thank you, please take care too.",
    "have a good day":  "Thank you, please have a good day too!",
    "have a nice day":  "Thank you, please have a nice day too!",
    "have a great day": "Thank you, please have a great day too!",
    "thank you":        "You are welcome, please.",
    "thanks":           "No problem at all, please.",
    "medaase":          "God bless you too, please! You are most welcome.",
    "sorry":            "Please, no worries at all.",
    "excuse me":        "Please, no problem at all.",
    "i appreciate it":  "You are welcome, please.",
    "nice to meet you": "Please, nice to meet you too!",
    "pleased to meet you": "Please, the pleasure is mine!",
}

NAME_CALLED_REPLIES = [
    "Yes please!",
    "Yes please, go ahead!",
    "Please, yes! How can I help?",
    "I am here, please!",
    "Yes, please speak!",
]

ACKNOWLEDGMENT_POOL = [
    "Okay...",
    "I see...",
    "Really?",
    "Oh wow...",
    "Go on...",
    "And then?",
    "Is that so?",
    "Interesting...",
    "I understand...",
    "Tell me more...",
    "I am listening...",
    "That is something...",
]

EMOTIONAL_ACKNOWLEDGMENTS_POSITIVE = [
    "Oh that is wonderful!",
    "I am so happy for you!",
    "That must have been amazing!",
    "That is really great news!",
    "I am glad to hear that!",
]

EMOTIONAL_ACKNOWLEDGMENTS_NEGATIVE = [
    "Oh no, that is terrible!",
    "I am so sorry to hear that!",
    "That sounds really tough!",
    "I hope things get better soon!",
    "Please stay strong!",
]

GHANAIAN_SURPRISE_REPLIES = [
    "Oh wow, is that so?",
    "Really? Tell me more!",
    "Oh wow, go on please!",
    "Is that so? Interesting!",
]

FALLBACK_AMBIGUOUS = [
    "I see...",
    "Oh really?",
    "Is that so?",
    "Interesting...",
    "I understand...",
    "Tell me more",
    "Go on...",
    "And then?",
]

FALLBACK_UNCLEAR = [
    "Sorry, could you repeat that?",
    "I did not catch that clearly",
    "Could you speak a bit slower please?",
    "Please could you say that again?",
    "I am sorry, could you say that once more?",
]

EMERGENCY_REPLIES = [
    "I NEED HELP",
    "PLEASE CALL SOMEONE",
    "EMERGENCY — PLEASE HELP",
]

# =============================================================================
# CULTURAL REPLIES
# =============================================================================

def get_how_are_you_reply():
    religion = get_setting("user_religion", "Christian")
    if religion == "Christian":
        return "I am fine by God's grace, please!"
    elif religion == "Muslim":
        return "I am fine, Alhamdulillah, please!"
    else:
        return "I am fine, thank you!"

def get_farewell_blessing():
    religion = get_setting("user_religion", "Christian")
    if religion == "Christian":
        return "Go well, God be with you!"
    elif religion == "Muslim":
        return "Go well, Allah be with you!"
    else:
        return "Go well, please take care!"

def get_deaf_explanation():
    name = get_setting("user_name", "Edemi")
    return (
        f"Please, my name is {name}. "
        f"I am deaf and I use smart glasses to communicate. "
        f"Please speak normally and I will reply here."
    )

# =============================================================================
# INTENT DETECTION
# =============================================================================

def detect_intent(text):
    t = text.lower().strip()
    user_name = get_setting("user_name", "").lower()

    # Priority 1 — urgent
    if any(w in t for w in URGENT_WORDS):
        return "urgent"

    # Priority 2 — deaf explanation trigger
    if any(p in t for p in DEAF_TRIGGER_PHRASES):
        return "deaf_explain"

    # Priority 3 — identity
    if any(p in t for p in IDENTITY_PHRASES):
        return "identity"

    # Priority 4 — name called
    if user_name and user_name in t:
        return "name_called"

    # Priority 5 — how are you (before greeting to avoid misfire)
    if any(p in t for p in HOW_ARE_YOU_PHRASES):
        return "how_are_you"

    # Priority 6 — specific intents
    if any(w in t for w in GREETING_WORDS):
        return "greeting"

    if any(w in t for w in FAREWELL_WORDS):
        return "farewell"

    if any(w in t for w in CONCERN_WORDS):
        return "concern"

    if any(w in t for w in GRATITUDE_WORDS):
        return "thanks"

    if any(w in t for w in APOLOGY_WORDS):
        return "apology"

    if any(p in t for p in REPEAT_PHRASES):
        return "repeat_request"

    if any(p in t for p in AGREEMENT_PHRASES):
        return "agreement"

    if any(p in t for p in DISAGREEMENT_PHRASES):
        return "disagreement"

    if any(p in t for p in COMPLIMENT_PHRASES):
        return "compliment"

    if any(p in t for p in LOCATION_PHRASES):
        return "location"

    if any(p in t for p in PAYMENT_PHRASES):
        return "payment"

    if any(p in t for p in WAITING_PHRASES):
        return "waiting"

    if any(p in t for p in PERMISSION_PHRASES):
        return "permission"

    if any(p in t for p in INVITATION_PHRASES):
        return "invitation"

    if any(p in t for p in OPINION_PHRASES):
        return "opinion"

    if any(p in t for p in HELP_PHRASES):
        return "help_offer"

    if any(p in t for p in FOOD_PHRASES):
        return "food"

    if any(w in t for w in GHANAIAN_SURPRISE):
        return "ghanaian_surprise"

    if any(w in t for w in EMOTIONAL_WORDS_POSITIVE + EMOTIONAL_WORDS_NEGATIVE):
        return "emotional_statement"

    if any(t.startswith(s) for s in QUESTION_STARTERS):
        return "question"

    if text.strip().endswith("?"):
        return "question"

    if any(t.startswith(c) for c in STORY_CONNECTORS):
        return "story"

    if any(t.endswith(e) for e in INCOMPLETE_ENDINGS):
        return "incomplete"

    if any(f in t for f in THINKING_FILLERS):
        return "thinking"

    if any(w in t for w in INSTRUCTION_WORDS):
        return "instruction"

    if len(t.split()) >= 3:
        return "statement"

    return "unclear"


def detect_confidence(text):
    t = text.lower().strip()
    words = t.split()
    if len(words) < 2:
        return "unclear"
    if "[unk]" in t:
        return "unclear"
    if len(set(words)) == 1:
        return "unclear"
    if any(t.endswith(e) for e in INCOMPLETE_ENDINGS):
        return "incomplete"
    if all(w in THINKING_FILLERS for w in words):
        return "unclear"
    return "confident"


def should_generate_suggestions(intent, confidence):
    if intent == "urgent":
        return "emergency"

    # Single-word known intents are unambiguous — bypass confidence gate
    UNAMBIGUOUS_INTENTS = [
        "greeting", "farewell", "thanks", "apology",
        "how_are_you", "deaf_explain", "identity",
        "repeat_request", "agreement", "disagreement",
        "compliment", "waiting", "ghanaian_surprise",
        "name_called"
    ]
    if confidence == "unclear" and intent not in UNAMBIGUOUS_INTENTS:
        return "auto_unclear"

    if confidence == "incomplete" or intent in ["incomplete", "thinking"]:
        return "none"

    # Tier 1 — full auto reply, no user selection needed
    if intent in [
        "greeting", "farewell", "thanks", "apology",
        "how_are_you", "deaf_explain", "identity",
        "repeat_request", "agreement", "disagreement",
        "compliment", "waiting", "ghanaian_surprise"
    ]:
        return "auto_social"

    if intent == "name_called":
        return "auto_name"

    if intent in ["story", "statement", "emotional_statement"]:
        return "auto_ack"

    # Tier 2 — smart suggestions, user selects
    if intent in [
        "question", "instruction", "concern",
        "location", "payment", "permission",
        "invitation", "opinion", "help_offer", "food"
    ]:
        return "prompted"

    return "auto_ambiguous"


# =============================================================================
# REPLY GENERATION
# =============================================================================

_last_acknowledgment = ""


def get_auto_social_reply(text, intent):
    t = text.lower().strip()

    if intent == "deaf_explain":
        return get_deaf_explanation()

    if intent == "identity":
        name = get_setting("user_name", "Edemi")
        return f"Please, my name is {name}. Nice to meet you!"

    if intent == "how_are_you":
        return get_how_are_you_reply()

    if intent == "farewell":
        return get_farewell_blessing()

    if intent == "repeat_request":
        return "Please, I am sorry. Could you say that again more clearly?"

    if intent == "agreement":
        return random.choice([
            "Please, yes! I agree completely.",
            "That is correct, please.",
            "Yes please, exactly right!",
        ])

    if intent == "disagreement":
        return random.choice([
            "Please, I understand your point.",
            "I see, please tell me more.",
            "That is interesting, please go on.",
        ])

    if intent == "compliment":
        return random.choice([
            "Thank you so much, please!",
            "Please, that is very kind of you!",
            "Thank you, I appreciate that please!",
        ])

    if intent == "waiting":
        return random.choice([
            "Please, no problem! Take your time.",
            "Of course please, I will wait.",
            "Please, no rush at all!",
        ])

    if intent == "ghanaian_surprise":
        return random.choice(GHANAIAN_SURPRISE_REPLIES)

    # Check direct trigger map
    for trigger, reply in AUTO_SOCIAL_REPLIES.items():
        if trigger in t:
            return reply

    return None


def get_name_reply(text):
    t = text.lower()
    if any(c in t for c in CONCERN_WORDS):
        return get_how_are_you_reply()
    if any(g in t for g in GREETING_WORDS):
        return "Please, hello! How can I help?"
    return random.choice(NAME_CALLED_REPLIES)


def get_acknowledgment(text, intent):
    global _last_acknowledgment
    t = text.lower()

    if intent == "emotional_statement":
        if any(w in t for w in EMOTIONAL_WORDS_POSITIVE):
            pool = EMOTIONAL_ACKNOWLEDGMENTS_POSITIVE
        elif any(w in t for w in EMOTIONAL_WORDS_NEGATIVE):
            pool = EMOTIONAL_ACKNOWLEDGMENTS_NEGATIVE
        else:
            pool = ACKNOWLEDGMENT_POOL
    else:
        pool = ACKNOWLEDGMENT_POOL

    available = [a for a in pool if a != _last_acknowledgment]
    if not available:
        available = pool

    ack = random.choice(available)
    _last_acknowledgment = ack
    return ack


def get_prompted_suggestions(text, intent):
    t = text.lower().strip()
    city = get_setting("user_city", "")

    # CONCERN
    if intent == "concern":
        return [
            get_how_are_you_reply(),
            "Please, I am doing well thank you!",
            "I am okay, thank you for asking!"
        ]

    # TIME
    if any(p in t for p in ["what time", "what's the time", "current time"]):
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        return [
            f"It is {time_str} please.",
            f"The time is {time_str}.",
            "I am not sure of the time."
        ]

    # DATE
    if any(p in t for p in ["what day", "what's the date", "what is the date", "today's date"]):
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %B %d")
        return [
            f"Today is {date_str}.",
            f"It is {date_str}.",
            "I am not sure of the date."
        ]

    # LOCATION
    if intent == "location":
        if city:
            return [
                f"Please, I am in {city}. Try Google Maps for directions.",
                "I am sorry, I do not know this area well.",
                "Please ask someone nearby, they can help better."
            ]
        else:
            return [
                "I am sorry, I do not know the directions.",
                "Please try Google Maps for directions.",
                "Please ask someone nearby, they can help."
            ]

    # PAYMENT
    if intent == "payment":
        return [
            "Please, I do not have the exact amount.",
            "Mobile money is fine please.",
            "Please, can you check the price for me?"
        ]

    # PERMISSION
    if intent == "permission":
        return [
            "Yes of course, please go ahead.",
            "No problem at all, please.",
            "Please, yes you may."
        ]

    # INVITATION
    if intent == "invitation":
        return [
            "Yes I would love to, thank you!",
            "Thank you but I cannot make it.",
            "When is it exactly please?"
        ]

    # OPINION
    if intent == "opinion":
        return [
            "Please, I think it is very good.",
            "I agree completely, please.",
            "That is interesting, please tell me more."
        ]

    # HELP OFFER
    if intent == "help_offer":
        return [
            "Yes please, thank you!",
            "No thank you, I am fine.",
            "Please, I would appreciate that."
        ]

    # FOOD / DRINK
    if intent == "food":
        return [
            "Yes please, thank you!",
            "No thank you.",
            "Maybe later please."
        ]

    # GENERAL QUESTION — short
    if text.strip().endswith("?") and len(text.split()) <= 5:
        return [
            "Yes please.",
            "No thank you.",
            "I am not sure, please."
        ]

    # INSTRUCTION
    if intent == "instruction":
        return [
            "Understood, please.",
            "I will do that.",
            "Got it, thank you."
        ]

    # GENERAL QUESTION — longer
    if intent == "question":
        return [
            "Could you tell me more please?",
            "Please, let me think about that.",
            "That is a good question, please."
        ]

    # DEFAULT FALLBACK SUGGESTIONS
    return [
        "Could you repeat that please?",
        "Please, can you write it down?",
        "One moment please."
    ]


def get_fallback_reply(confidence):
    global _last_acknowledgment
    pool = FALLBACK_UNCLEAR if confidence == "unclear" else FALLBACK_AMBIGUOUS
    available = [r for r in pool if r != _last_acknowledgment]
    if not available:
        available = pool
    reply = random.choice(available)
    _last_acknowledgment = reply
    return reply


def get_emergency_replies():
    e1 = get_setting("emergency_message_1", "I NEED HELP")
    e2 = get_setting("emergency_message_2", "PLEASE CALL SOMEONE")
    e3 = get_setting("emergency_message_3", "EMERGENCY — PLEASE HELP")
    return [e1, e2, e3]


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def process_speech(text, history=None):
    """
    Main function called by speech engine.
    Returns dict with reply_type and content.
    Only fires on final Vosk results — not partials.
    """
    if not text or not text.strip():
        return {"reply_type": "none", "content": None}

    if history is None:
        history = []

    intent     = detect_intent(text)
    confidence = detect_confidence(text)
    category   = should_generate_suggestions(intent, confidence)

    if category == "emergency":
        return {"reply_type": "emergency",
                "content": get_emergency_replies(),
                "intent": intent}

    if category == "auto_social":
        reply = get_auto_social_reply(text, intent)
        if not reply:
            reply = get_fallback_reply(confidence)
        return {"reply_type": "auto_social",
                "content": reply,
                "intent": intent,
                "delay": 0.5}

    if category == "auto_name":
        return {"reply_type": "auto_name",
                "content": get_name_reply(text),
                "intent": intent,
                "delay": 0.3}

    if category == "auto_ack":
        return {"reply_type": "auto_ack",
                "content": get_acknowledgment(text, intent),
                "intent": intent,
                "delay": 1.5}

    if category in ["auto_unclear", "auto_ambiguous"]:
        return {"reply_type": category,
                "content": get_fallback_reply(confidence),
                "intent": intent,
                "delay": 0.5}

    if category == "prompted":
        return {"reply_type": "prompted",
                "content": get_prompted_suggestions(text, intent),
                "intent": intent}

    if category == "none":
        return {"reply_type": "none", "content": None, "intent": intent}

    return {"reply_type": "none", "content": None, "intent": intent}
