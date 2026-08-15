"""Day 9 routing and handoff checks — no network, no LiveKit session, no LLM.

Step 6 asks for both paths tested: a normal question stays with Rishika, a PID
question goes to Kabir. The ten-request table below is the optional routing test.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import specialists
from agent import Assistant

# Ten real things a learner says. True = must be allowed through to the PID coach.
ROUTING_CASES = [
    # Stay with Rishika — she owns all of this.
    ("मेरा IR sensor threshold कैसे set करूं?", False),
    ("L298N की wiring order क्या है?", False),
    ("Mujhe ek quiz question do", False),
    ("What does duty cycle mean?", False),
    ("मेरे motor driver से जलने की स्मेल आ रही है", False),
    # Go to Kabir — PID gains and line-tracking stability.
    ("मेरा रोबोट लाइन पर ज़िग-ज़ैग कर रहा है", True),
    ("Kp kitna rakhna chahiye?", True),
    ("The robot overshoots every curve", True),
    ("Ki और Kd में क्या फर्क है?", True),
    ("My line follower keeps oscillating around the line", True),
]


def test_ten_sample_requests_route_to_the_right_agent():
    """Optional advanced item: every one of the ten stays or goes, deliberately."""
    for text, expected in ROUTING_CASES:
        assert specialists.needs_pid_coach(text) is expected, f"misrouted: {text!r}"


def test_a_normal_question_is_refused_by_the_handoff_tool():
    """Step 6: the guard is in code, so an over-eager LLM cannot hand off an IR question."""
    main = Assistant()
    result = _call(main.transfer_to_pid_specialist, "मेरा IR sensor threshold कैसे set करूं?")

    assert isinstance(result, str), "a non-PID request must not produce an agent switch"
    assert result.startswith("NOT_TRANSFERRED")
    assert "yours to answer" in result


def test_a_pid_question_produces_the_specialist_with_the_conversation_attached():
    """Steps 2, 3 and 4: a real handoff, and the specialist already knows the problem."""
    main = Assistant()
    main.learner = "Ramesh"
    # What was already said before the handoff. Seeded directly — no live session here.
    main._chat_ctx.add_message(role="user", content="मैं रमेश हूँ, मेरी रोबोट कार बनी है")
    main._chat_ctx.add_message(role="assistant", content="नमस्ते रमेश!")

    request = "मेरा रोबोट लाइन पर ज़िग-ज़ैग कर रहा है"
    coach = _call(main.transfer_to_pid_specialist, request)

    assert isinstance(coach, specialists.PIDCoach), "a PID request must switch agents"
    assert coach.main is main, "the specialist must be able to hand back"
    assert request in coach.instructions, "the specialist must be told what was asked"
    assert "Ramesh" in coach.instructions, "saved learner details travel with the handoff"

    # The conversation travels with the learner — this is why they never repeat it.
    carried = [m.text_content for m in coach.chat_ctx.items if m.type == "message"]
    assert "मैं रमेश हूँ, मेरी रोबोट कार बनी है" in carried
    assert len(carried) == 2


def test_the_specialist_is_narrower_than_the_main_agent():
    """Step 1 and 2: different, clear jobs — and PID is not in Rishika's tool list."""
    main = Assistant()
    coach = specialists.PIDCoach(main=main)

    main_tools = {t.info.name for t in main.tools}
    coach_tools = {t.info.name for t in coach.tools}

    assert "transfer_to_pid_specialist" in main_tools
    assert coach_tools == {"hand_back_to_rishika"}, "the specialist has exactly one exit"
    assert len(coach_tools) < len(main_tools)
    assert "Kabir" in coach.instructions and "PID" in coach.instructions


def test_the_specialist_sounds_different():
    """A handoff you can hear: Kabir overrides the session voice with a male one."""
    coach = specialists.PIDCoach(main=Assistant())

    assert coach.tts is not None, "the coach must carry his own TTS, not inherit Anisha"
    assert coach.tts._opts.voice == "Samar"


def test_pid_is_never_spoken_as_one_word():
    """Murf says 'pid' if you hand it PID — every spoken path spells the letters out."""
    import static_intents

    assert "PID" not in static_intents.HANDOFF_TO_PID_FILLER
    assert "पी आई डी" in static_intents.HANDOFF_TO_PID_FILLER
    # The rule has to reach the LLM too, or it will write PID back into its replies.
    assert "पी आई डी" in specialists.PID_COACH_PROMPT


def test_the_specialist_hands_the_conversation_back():
    """Advanced: the coach returns the learner to Rishika when the topic changes."""
    main = Assistant()
    coach = specialists.PIDCoach(main=main, learner_request="robot wobbles")

    returned, message = _call(coach.hand_back_to_rishika, "they now want a quiz")

    assert returned is main, "hand-back must reuse the same main agent instance"
    assert "quiz" in message, "Rishika must be told what they need now"
    assert "repeat" in message, "the learner must not be asked to explain it again"


def test_a_failed_handoff_leaves_rishika_helping(monkeypatch):
    """Advanced: if the specialist cannot start, the learner is not left in a dead end."""
    def boom(**kwargs):
        raise RuntimeError("specialist unavailable")

    monkeypatch.setattr(specialists, "PIDCoach", boom)
    result = _call(Assistant().transfer_to_pid_specialist, "Kp kitna rakhna chahiye?")

    assert isinstance(result, str)
    assert result.startswith("HANDOFF_FAILED")
    assert "yourself" in result, "she must be told to carry on with the tuning herself"


def _call(tool, *args):
    """Invoke a @function_tool directly, with no RunContext and no live session."""
    import asyncio

    return asyncio.run(tool(None, *args))
