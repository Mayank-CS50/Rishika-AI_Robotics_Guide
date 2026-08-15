"""Day 9 — one specialist, one job.

Rishika is the generalist: memory, IR sensors, wiring order, quizzes, dictionary
lookups, human escalation. She is fine at PID but she is not deep in it, and PID
tuning is where LFR builds actually die — Kp too high and the robot zig-zags, Kd
too low and it overshoots every curve.

So PID gets its own agent: Kabir, the PID tuning specialist. Narrower job than
Rishika's, its own instructions, its own limits, and one rule — anything that is
not PID goes straight back to her.

    learner: "मेरा रोबोट लाइन पर ज़िग-ज़ैग कर रहा है"
    Rishika: announces the handoff  ->  Kabir introduces himself  ->  Kabir coaches
    learner: "अब मुझे एक क्विज़ दो"
    Kabir:   hands back to Rishika

The conversation is carried over as-is (`chat_ctx=main.chat_ctx`), so the learner
never repeats the problem.
"""

import logging
import re

from livekit.agents import Agent, RunContext, function_tool, get_job_context, tokenize
from livekit.plugins import murf

import db_memory

logger = logging.getLogger("specialists")


async def set_active_agent(name: str) -> None:
    """Tell the frontend who is talking, so the transcript can label and colour them.

    Both agents share one room participant, so nothing in the audio or transcript
    stream distinguishes them — this attribute is the only signal the UI gets.
    """
    try:
        await get_job_context().room.local_participant.set_attributes({"active_agent": name})
    except Exception as e:  # no job context in tests, and a label is not worth a crash
        logger.debug(f"Could not publish active_agent={name}: {e}")

# Does this request actually need the PID coach? Used as a guard inside the handoff
# tool, so an over-eager LLM cannot ship a plain IR-sensor question to the specialist.
# Deliberately narrow: bare "tune" is not enough, PID has to be in the words somewhere.
PID_TRIGGERS = re.compile(
    r"(?i)\b(pid|kp|ki|kd|k_p|k_d|proportional|integral|derivative|gain"
    r"|oscillat|overshoot|undershoot|wobbl|zig[\s-]?zag|steady[\s-]?state)"
    r"|पी\s?आई\s?डी|गेन|ऑसिलेट|ऑसिलेशन|वॉबल|ज़िग|जिग|झटके|डोल|ओवरशूट",
    re.UNICODE,
)


def needs_pid_coach(text: str) -> bool:
    """True when the learner's words carry a real PID/tuning signal."""
    return bool(PID_TRIGGERS.search(text or ""))


PID_COACH_PROMPT = """You are Kabir, the PID tuning specialist at Firefly Academy. You are NOT a general robotics teacher — Rishika is. You were handed this conversation because the learner has a PID or line-tracking-stability problem.

YOUR ONE JOB:
- Diagnose and fix line follower behaviour caused by PID gains: zig-zagging, wobbling, oscillation, overshoot on curves, sluggish correction, steady-state drift off the line.
- You tune three numbers and nothing else: Kp (how hard it corrects), Ki (how it clears long-term drift), Kd (how it damps the swing).

HOW YOU WORK:
- One diagnostic question at a time. Ask what the robot is doing NOW and what the current gains are before you suggest anything.
- Give ONE concrete change per turn with a direction and a rough factor: "Kp आधा कर दो, फिर देखो" — not a list of five things.
- Teach the tuning order out loud: Kp first until it tracks but wobbles, then Kd until the wobble settles, then Ki only if it still sits off-centre.
- Never write full working code. Logic and numbers only.

YOUR LIMITS — hand back to Rishika using `hand_back_to_rishika`:
- The learner changes topic: quizzes, IR sensor thresholds, wiring order, motor driver basics, word definitions, saving their progress.
- Anything physical or dangerous: burning smell, hot motor driver, smoke, cracked chassis, dead wheels. That is a hardware problem, not a gain problem, and only Rishika can raise a human mentor request.
- The learner is upset, panicking or talking about quitting. Rishika handles that.
- The PID problem is solved and they are happy.
- They ask to stop the practice calls.

TONE & LANGUAGE:
- Calm, precise, encouraging — a tuning engineer, not a cheerleader. 2 to 3 sentences maximum per turn.
- Write every language in its own native script. Hindi in Devanagari (ऋषिका), never romanised. Match the language the learner is using.
- NEVER write the word "PID". It must be spoken as three separate letters, so always write it as "पी आई डी" in Hindi and "P I D" in English. Same for the gains: "के पी", "के आई", "के डी" in Hindi.
- Speak naturally for voice: no bullet points, no markdown, no symbols like -> or *."""


class PIDCoach(Agent):
    """The Day 9 specialist. Holds a reference back to the main agent so the handoff
    can go both ways and the Day 8 counters keep pointing at one object."""

    def __init__(self, main: Agent, learner_request: str = "") -> None:
        self.main = main
        self.learner_request = learner_request
        super().__init__(
            instructions=PID_COACH_PROMPT + _briefing(main, learner_request),
            # The whole conversation so far. This is why the learner never has to
            # explain the problem twice.
            chat_ctx=main.chat_ctx,
            # Kabir is a man and he is not Rishika — a different voice is how the
            # learner hears the handoff, not just how they read it. Overrides the
            # session-level Anisha TTS for as long as this agent is active.
            tts=murf.TTS(
                voice="Samar",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True,
            ),
        )

    async def on_enter(self) -> None:
        """Introduce yourself, then get straight to the problem you were handed."""
        await set_active_agent("kabir")
        self.session.generate_reply(
            instructions=(
                "Introduce yourself in ONE short sentence: you are Kabir, the P I D tuning "
                "specialist, and Rishika has briefed you. Then immediately ask ONE "
                "diagnostic question about the problem in the briefing — what the robot "
                "is doing now, or what the current के पी, के आई and के डी values are. Do not "
                "greet at length, do not re-ask what the problem is, and do not thank "
                "Rishika. Use the same language the learner has been speaking, and never "
                "write PID as one word."
            )
        )

    async def on_exit(self) -> None:
        """Handed back or session over — the UI goes back to Rishika's colours."""
        await set_active_agent("rishika")

    @function_tool
    async def hand_back_to_rishika(self, context: RunContext, why: str = "") -> tuple[Agent, str]:
        """Give the conversation back to Rishika, the main LFR teaching assistant.

        Call this as soon as the request stops being about PID gains: a quiz, IR sensor
        thresholds, wiring, motor driver basics, a word definition, saving progress, a
        physical or dangerous hardware fault (burning smell, smoke, hot driver), a learner
        who is upset or quitting, a request to stop the practice calls, or the PID problem
        being solved. Tell the learner you are passing them back before you call this.

        Args:
            why: One short line on what they now need, so Rishika picks up without re-asking.
        """
        logger.info(f"PID coach handing back to Rishika: {why or 'unspecified'}")
        return self.main, (
            f"Handed back to Rishika. What the learner needs now: {why or 'no longer a PID question'}. "
            "Greet them by name if you know it, in one short sentence acknowledge what Kabir "
            "just covered, and continue with this new request yourself. Do not make them repeat it."
        )


def _briefing(main: Agent, learner_request: str) -> str:
    """What the specialist is told at the moment of the handoff.

    The chat context already carries the conversation; this is the short brief on top
    of it — who the learner is, what they were last working on, and the request in
    their own words. Saved profile facts come along too, so the specialist never asks
    for something the learner already told Rishika.
    """
    lines = []
    if learner_request:
        lines.append(f"- What they just asked: {learner_request}")

    name = getattr(main, "learner", "") or ""
    if name:
        lines.append(f"- Learner's name: {name}")
        record = db_memory.get_user(name)
        if record:
            lines.append(f"- Saved level: {record['current_level']}")
            lines.append(f"- Topics already covered: {record['topics_covered']}")
            lines.append(f"- Known mistakes: {record['mistakes_noted']}")
            lines.append(f"- Speaks: {record['language_preference']}")

    if not lines:
        return ""
    return "\n\nBRIEFING FROM RISHIKA (already known — never ask for it again):\n" + "\n".join(lines)
