import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class StaticResponse:
    text: str
    intent_type: str  # 'greeting', 'farewell'


# Regex patterns for pure greetings and farewells (English & Devanagari Hindi)
GREETING_PATTERNS = [
    r"^(hi|hello|hey|namaste|namaskar|helo|hlo|hii|hiii)(\s+(rishika|rishi|ta|bot|assistant))?[!.\s]*$",
    r"^(नमस्ते|नमस्कार|हेलो|हे)(\s+(ऋषिका|ऋषि))?[!.\s]*$",
]

FAREWELL_PATTERNS = [
    r"^(bye|goodbye|bye\s+bye|see\s+ya|cya|take\s+care|tata)(\s+(rishika|rishi))?[!.\s]*$",
    r"^(बाय|बाय\s+बाय|अलविदा|फिर\s+मिलेंगे)[!.\s]*$",
]

# Static responses for ultra-fast direct TTS execution (0 LLM tokens, ~50ms latency)
GREETING_RESPONSES = [
    "नमस्ते! मैं ऋषिका हूँ, आपकी LFR टीचिंग असिस्टेंट! लाइन फॉलोअर रोबॉट्स के बारे में आप क्या पूछना चाहते हैं?",
]

FAREWELL_RESPONSES = [
    "बाय! रोबोटिक्स प्रोजेक्ट्स बनाते रहिए और कोई भी डाउट हो तो मुझसे ज़रूर पूछिए। टेक केयर!",
]

# Tool execution filler statements (spoken while async tool is running)
LOOKUP_USER_FILLER = "एक सेकंड, मैं आपका रिकॉर्ड चेक कर रही हूँ..."
SAVE_USER_FILLER = "ठीक है, मैं आपकी प्रोग्रेस और डिटेल्स सेव कर रही हूँ..."
FORGET_USER_FILLER = "एक मिनट, मैं आपका डेटा डिलीट कर रही हूँ..."
DICTIONARY_LOOKUP_FILLER = "एक सेकंड, मैं डिक्शनरी में शब्द की परिभाषा चेक कर रही हूँ..."
QUIZ_FETCH_FILLER = "ठीक है, मैं आपके लिए साइंस और रोबोटिक्स क्विज़ का सवाल निकाल रही हूँ..."
ESCALATION_FILLER = "ठीक है, मैं आपकी रिक्वेस्ट मेंटर के लिए तैयार कर रही हूँ..."

# Day 9: spoken by Rishika via session.say, so the learner is always told about the
# handoff in the same words — the LLM cannot paraphrase the announcement away.
# "पी आई डी" and not "PID": spelled out so Murf reads three letters, not one word.
HANDOFF_TO_PID_FILLER = (
    "ये पी आई डी ट्यूनिंग का मामला है, तो मैं आपको हमारे पी आई डी स्पेशलिस्ट कबीर से कनेक्ट कर रही हूँ। "
    "एक सेकंड..."
)


def outbound_opening(student_name: str = "", last_topic: str = "") -> str:
    """Day 6 opening script. First two sentences must say who is calling, why, and how to stop.

    Spoken via session.say() rather than the LLM so the disclosure is never paraphrased away.
    """
    greeting = f"नमस्ते {student_name}!" if student_name else "नमस्ते!"
    why = (
        f"पिछली बार हमने {last_topic} पर बात की थी, तो आज उसकी प्रैक्टिस करवाने के लिए कॉल किया है।"
        if last_topic
        else "आपकी लाइन फॉलोअर रोबोट की डेली प्रैक्टिस के लिए कॉल किया है।"
    )
    return (
        f"{greeting} मैं ऋषिका बोल रही हूँ, Firefly Academy से — आपकी LFR टीचिंग असिस्टेंट। "
        f"{why} "
        "अगर आप आगे ये कॉल्स नहीं चाहते, तो बस कह दीजिए 'स्टॉप कॉलिंग' और मैं आपका नंबर हमेशा के लिए हटा दूँगी। "
        "तो बताइए, आज प्रैक्टिस करने का टाइम है?"
    )


def match_static_intent(transcript: str) -> Optional[StaticResponse]:
    """Matches a user transcript against static regex patterns.

    Returns a StaticResponse if matched, or None if the input should be handled by the LLM.
    """
    if not transcript:
        return None

    cleaned_text = transcript.strip().lower()

    # Check greetings
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, cleaned_text, re.IGNORECASE):
            return StaticResponse(
                text=GREETING_RESPONSES[0],
                intent_type="greeting",
            )

    # Check farewells
    for pattern in FAREWELL_PATTERNS:
        if re.search(pattern, cleaned_text, re.IGNORECASE):
            return StaticResponse(
                text=FAREWELL_RESPONSES[0],
                intent_type="farewell",
            )

    return None
