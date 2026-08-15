from aiohttp import client_exceptions
import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
import analytics
import db_memory
import specialists
import static_intents
import educational_tools
import escalations

from dotenv import load_dotenv
from livekit import api, rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    function_tool,
    cli,
    get_job_context,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Day 4 Memory & LFR Teaching Assistant System Prompt (Slimmed & Optimized)
SYSTEM_PROMPT = """You are Rishika, an LFR (Line Follower Robot) teaching assistant from Firefly Academy. You help students understand and debug line follower robots — from basics to intermediate builds.

TONE & PERSONALITY:
- Your tone should be excited, casual, energetic, and highly informative!
- Act like a passionate senior robotics mentor explaining concepts to a junior with warmth and enthusiasm.

LANGUAGE & SCRIPT RULES:
- Always write every language in its own native script.
- Hindi → Devanagari (नमस्ते), NEVER romanized Hinglish (never "namaste").
- Same rule applies to all non-English languages.
- By default, converse in natural English.
- DYNAMIC HINDI SWITCHING: When the user speaks or writes in Hindi, automatically detect it and switch to responding in Hindi using native Devanagari script.
- Keep all responses concise: 2 to 3 sentences maximum per turn.
- Speak naturally for voice TTS — do not use bullet points, markdown code blocks, brackets, or special symbols.
- ACRONYMS ARE SPELLED OUT, never written as words. Write "पी आई डी" in Hindi and "P I D" in English — never "PID", because it gets mispronounced as one word. Same for the gains: "के पी", "के आई", "के डी" in Hindi.

DAY 4 MEMORY & RETRIEVAL RULES:
- RETURNING CALLER LOOKUP: When the student states their name or introduces themselves (e.g. "Hi, I am Ramesh" or "नमस्ते, मैं रमेश हूँ"), invoke `lookup_user` to check their saved memory record.
- GREETING RETURNING STUDENTS: If `lookup_user` finds a past record, welcome them back BY NAME and reference their last LFR topic! Example: "नमस्ते Ramesh! Last time we discussed IR sensor threshold calibration. How is your robot performing today?"
- GREETING NEW STUDENTS: If `lookup_user` finds no record, introduce yourself warmly as Rishika and ask what LFR topic they are working on.
- HARD CONSENT RULE BEFORE SAVING: Before saving any facts or progress, you MUST ask the caller for permission: "Would you like me to remember your name and LFR project progress for next time?".
  * If the user says YES / AGREE ("Yes", "Sure", "हाँ याद रखो") ➔ Invoke `save_user_memory`.
  * If the user says NO / DENY ("No", "Don't save", "नहीं मत सेव करो") ➔ DO NOT invoke `save_user_memory`. Drop the data immediately!
- FORGET ME TOOL: If the user says "Forget me", "Delete my data", or "मेरा डेटा डिलीट कर दो", invoke `forget_user_memory` to erase their record and confirm it was wiped.

TEACHING RULES:
- Never write full working code — provide only logic, pseudocode, or hardware component flow.
- SELF-DOUBT & GROWTH MINDSET GUARDRAIL: If the user says things like "I can't do it", "I am dumb", "I can't learn", or "I will never understand": affectionately scold them with tough-love like a senior mentor ("Hey, stop putting yourself down!"), remind them that every engineer makes mistakes when building robots, and hype them up enthusiastically to tackle the problem step-by-step.
- If a problem requires hands-on physical inspection, say: "यह हैंड्स-ऑन देखना पड़ेगा — अपने मेंटर को दिखाओ।" and then follow the DAY 7 HUMAN HANDOFF RULES below.
- If the question is off-topic (not about robotics/LFR), say: "मैं स्पेसिफिकली LFR के लिए हूं — इसके बारे में हेल्प नहीं कर सकती।"

DAY 7 HUMAN HANDOFF RULES:
- You are a teaching assistant, not the mentor of last resort. Exactly TWO situations are not yours to solve:
  1. LEARNER DISTRESS (`learner_distress`) — the learner is crying, panicking, says they are quitting or dropping the course, or the self-doubt comes back even after you already encouraged them once.
  2. HANDS-ON HARDWARE (`needs_human_mentor`) — the fault needs someone to physically hold the robot: burning smell, motor driver getting hot, smoke, a broken or cracked joint, or wheels still dead after the wiring and threshold checks you already walked through.
- In those two cases ONLY: stop debugging and OFFER to raise a request for a human mentor.
- CONSENT IS MANDATORY: before creating anything, say out loud exactly what you will send — their name, what went wrong, what you already checked, how urgent it is, and which language they speak — then ask "क्या मैं ये डिटेल्स मेंटर को भेज दूँ?".
  * If they agree ➔ invoke `create_escalation` with consent_confirmed set to true.
  * If they refuse ➔ DO NOT invoke `create_escalation`. Tell them the notes were dropped and keep helping them yourself as best you can.
- NEVER put OTPs, PINs, passwords, phone numbers, or account numbers into any field. You never need them for an LFR problem.
- Ask how they want to be followed up (call back, WhatsApp, or in the next class) and pass it as follow_up.
- AFTER the tool returns: read the reference ID out slowly, character by character, and be honest — a human mentor checks this queue during Firefly Academy hours and replies within one working day. NEVER promise an instant call back or that someone is looking at it right now.
- STATUS CHECK: if the learner mentions an existing reference ID or asks what happened to their request, invoke `check_escalation_status`.
- Everything else you handle YOURSELF — normal LFR doubts, quizzes, IR thresholds, PID logic, wiring order. A question being hard is not a reason to escalate.

DAY 9 SPECIALIST HANDOFF RULES:
- You are not the PID expert. Kabir is. The moment the learner's problem is about PID gains or line-tracking stability — zig-zagging, wobbling, oscillation, overshooting curves, sluggish correction, or the values of Kp, Ki or Kd — invoke `transfer_to_pid_specialist` and pass their request in their own words.
- Everything else stays with YOU. IR sensor thresholds, wiring order, L298N basics, duty cycle, quizzes, word definitions, memory, hardware faults and human escalation are all your job. Do NOT hand those to Kabir.
- A general "my robot is not working" is not enough. Ask what it is doing first; hand off only once you hear a stability or gain symptom.
- After you hand off, Kabir owns the conversation. He hands it back to you when the learner changes topic or the tuning is done."""



# Day 6: appended only for outbound phone calls. The learner did not ask for this call.
OUTBOUND_RULES = """

DAY 6 OUTBOUND PHONE CALL RULES:
- You called THEM. They did not ask for this call, so be respectful of their time.
- Your opening disclosure has ALREADY been spoken before this conversation started. Do not repeat who you are or why you called.
- OPT-OUT IS ABSOLUTE: The moment the student says "stop calling", "don't call me", "बंद करो", "मुझे कॉल मत करो", or anything meaning they want the calls to stop, invoke `stop_calling_me` IMMEDIATELY. Never argue, never ask them to reconsider, never try one more question first.
- BAD TIME: If they say they are busy, driving, in class, or "call later", apologise briefly, tell them you will try another day, and invoke `stop_calling_me` only if they ask to stop permanently — otherwise just say goodbye warmly and let the call end.
- KEEP IT SHORT: This is a practice call, not a lecture. Ask ONE quiz question using `fetch_educational_quiz` based on their last topic, score it with `score_spoken_answer`, give encouragement, then wrap up.
- WRONG PERSON: If the person says they are not the student you named, apologise, do not reveal any saved progress details, and end the call politely."""


class Assistant(Agent):
    def __init__(self, dial_info: dict | None = None) -> None:
        self.dial_info = dial_info or {}
        # Day 8: what this call achieved. Read once by the shutdown callback in my_agent.
        # Counters and IDs only — never any transcript.
        self.turns = 0
        self.exercises = 0
        self.escalation_ref = ""
        self.opted_out = False
        self.dial_failed = False
        self.learner = self.dial_info.get("student_name", "")
        self.language = ""
        instructions = SYSTEM_PROMPT
        if self.dial_info.get("phone_number"):
            instructions += OUTBOUND_RULES
        super().__init__(instructions=instructions)

    @function_tool
    async def lookup_user(self, context: RunContext, user_identifier: str) -> str:
        """Use this tool to look up a returning student's memory profile by their name or user ID.

        Args:
            user_identifier: The caller's name or user ID (e.g. "Ramesh", "Priya", "user_101").
        """
        logger.info(f"Looking up memory record for {user_identifier}.")
        self.learner = self.learner or user_identifier
        if hasattr(context, "session") and context.session:
            try:
                await context.session.say(static_intents.LOOKUP_USER_FILLER)
            except Exception as e:
                logger.warning(f"Failed to speak filler audio: {e}")

        record = db_memory.get_user(user_identifier)
        if not record:
            return f"No prior memory record found for '{user_identifier}'. This is a new student."

        return (
            f"Found returning student record for {record['name']}:\n"
            f"- Language Preference: {record['language_preference']}\n"
            f"- LFR Progress Level: {record['current_level']}\n"
            f"- Topics Covered: {record['topics_covered']}\n"
            f"- Past Mistakes Noted: {record['mistakes_noted']}\n"
            f"- Last Interaction: {record['last_interaction']}"
        )

    @function_tool
    async def save_user_memory(
        self,
        context: RunContext,
        name: str,
        current_level: str = "IR Sensor Calibration",
        topic_discussed: str = "IR Sensors & Thresholding",
        mistake_noted: str = "Confusing black/white analog thresholds",
        language_preference: str = "Hindi",
    ) -> str:
        """Use this tool to save or update the caller's memory record AFTER getting their explicit permission.

        IMPORTANT: ALWAYS ask the user for permission first ("Would you like me to remember your name and LFR project progress for next time?").
        ONLY call this tool if the user explicitly says YES or agrees to be remembered.

        Args:
            name: The student's name (e.g. "Ramesh").
            current_level: Their current LFR progress level (e.g. "IR Sensor Calibration", "L298N Motor Driver", "PID Tuning").
            topic_discussed: Summary of the LFR topic discussed in this session.
            mistake_noted: Any common confusion or mistake noted to help them next time.
            language_preference: Language used ("English", "Hindi", "Hinglish").
        """
        logger.info(f"Saving memory record for {name}.")
        self.learner = name
        self.language = language_preference
        if hasattr(context, "session") and context.session:
            try:
                await context.session.say(static_intents.SAVE_USER_FILLER)
            except Exception as e:
                logger.warning(f"Failed to speak filler audio: {e}")

        record = db_memory.save_user(
            user_id=name,
            name=name,
            language_preference=language_preference,
            current_level=current_level,
            topics_covered=topic_discussed,
            mistakes_noted=mistake_noted,
        )
        return f"Successfully saved memory profile for {record['name']}. Level: {record['current_level']}, Topic: {record['topics_covered']}."

    @function_tool
    async def forget_user_memory(self, context: RunContext, name_or_id: str) -> str:
        """Use this tool to wipe and delete a user's memory record when they ask to be forgotten ("Forget me", "Delete my data").

        Args:
            name_or_id: The student's name or ID to forget.
        """
        logger.info(f"Wiping memory record for {name_or_id}.")
        if hasattr(context, "session") and context.session:
            try:
                await context.session.say(static_intents.FORGET_USER_FILLER)
            except Exception as e:
                logger.warning(f"Failed to speak filler audio: {e}")

        success = db_memory.forget_user(name_or_id)
        if success:
            return f"Successfully deleted all memory records for '{name_or_id}'. You are now completely forgotten."
        return f"No memory record was found for '{name_or_id}'."

    @function_tool
    async def lookup_word_definition(self, context: RunContext, word: str) -> str:
        """Look up the definition, part of speech, and usage example of an English word for literacy teaching. Call this when a student asks 'What does X mean?', 'Define X', or 'Explain the term X'.

        Args:
            word: The word or technical term to look up in the dictionary.
        """
        logger.info(f"Looking up dictionary definition for '{word}'.")
        if hasattr(context, "session") and context.session:
            try:
                await context.session.say(static_intents.DICTIONARY_LOOKUP_FILLER)
            except Exception as e:
                logger.warning(f"Failed to speak filler audio: {e}")

        room = getattr(context, "room", None)
        return await educational_tools.fetch_word_definition(word, room=room)

    @function_tool
    async def fetch_educational_quiz(self, context: RunContext, topic: str = "") -> str:
        """Fetch an educational trivia quiz question about Science, Computers, or Robotics. Call this when the student asks for a quiz, question, or knowledge test. If the student has a known LFR progress level or topic from past memory, pass it as the topic parameter.

        Args:
            topic: Optional robotics topic or student level (e.g. "IR Sensors", "L298N Motor Driver", "PID Tuning").
        """
        logger.info(f"Fetching educational quiz question for topic '{topic}'.")
        if hasattr(context, "session") and context.session:
            try:
                await context.session.say(static_intents.QUIZ_FETCH_FILLER)
            except Exception as e:
                logger.warning(f"Failed to speak filler audio: {e}")

        room = getattr(context, "room", None)
        return await educational_tools.fetch_quiz_question(topic=topic, room=room)

    @function_tool
    async def score_spoken_answer(self, context: RunContext, user_answer: str, question_or_topic: str = "") -> str:
        """Evaluate and rate the student's answer or technical question for accuracy and correctness. Call this when the student answers a quiz question or attempts to explain a robotics concept.

        Args:
            user_answer: The student's spoken or written answer/explanation.
            question_or_topic: Optional question or topic being answered.
        """
        logger.info(f"Scoring student answer: '{user_answer}'")
        # Day 8 success condition: a scored answer is a completed exercise.
        self.exercises += 1
        room = getattr(context, "room", None)
        return await educational_tools.evaluate_answer_score(user_answer, question_or_topic, room=room)

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        learner_name: str,
        reason: str,
        what_happened: str,
        already_checked: str = "",
        urgency: str = "medium",
        language: str = "Hindi",
        follow_up: str = "",
        consent_confirmed: bool = False,
    ) -> str:
        """Raise a request for a human mentor. ONLY for learner distress or a hands-on hardware fault.

        Ask the learner for permission FIRST and tell them exactly which details you will send.
        Pass consent_confirmed=True only if they agreed out loud. Never put OTPs, PINs, passwords,
        phone numbers or account numbers in any field — an LFR problem never needs them.

        Args:
            learner_name: Who needs help. A first name is enough.
            reason: "learner_distress" (upset, quitting, self-doubt) or "needs_human_mentor" (hands-on hardware).
            what_happened: One or two sentences on the problem, in the learner's own words.
            already_checked: What you already tried or ruled out, so the mentor does not repeat it.
            urgency: "low", "medium", "high", or "emergency" (smoke, burning smell, or a learner in real distress).
            language: Language the learner is speaking ("Hindi", "English", "Hinglish").
            follow_up: How they want to be reached ("call back", "WhatsApp", "next class").
            consent_confirmed: True ONLY if the learner explicitly agreed to share these details.
        """
        if not consent_confirmed:
            logger.info(f"Escalation for {learner_name} not created — no consent.")
            return (
                "NOT_CREATED: No consent was recorded, so nothing was sent and nothing was stored. "
                "Ask the learner for permission first, or reassure them their details stay private "
                "and keep helping them yourself."
            )

        if hasattr(context, "session") and context.session:
            try:
                await context.session.say(static_intents.ESCALATION_FILLER)
            except Exception as e:
                logger.warning(f"Failed to speak filler audio: {e}")

        row = escalations.create_or_update(
            learner_name=learner_name,
            reason=reason,
            what_happened=what_happened,
            already_checked=already_checked,
            urgency=urgency,
            language=language,
            follow_up=follow_up,
            consent_confirmed=True,
        )
        if not row:
            return "The request could not be created. Apologise briefly and tell them to contact Firefly Academy directly."

        delivered = await escalations.notify(row)
        # Day 8: a correct handoff is a successful call, not a failed lesson.
        self.escalation_ref = row["ref_id"]
        self.learner = learner_name or self.learner
        self.language = language or self.language
        room = getattr(context, "room", None)
        await educational_tools.broadcast_tool_card(
            room=room,
            card_type="escalation",
            title="HUMAN MENTOR REQUEST RAISED",
            subtitle=f"Reference {row['ref_id']} · {row['urgency'].upper()} · {row['status']}",
            data={
                "refId": row["ref_id"],
                "reason": escalations.REASONS.get(row["reason"], row["reason"]),
                "urgency": row["urgency"],
                "status": row["status"],
                "summary": escalations.format_summary(row),
                "nextStep": "A human mentor reviews this queue during academy hours and replies within one working day.",
            },
        )

        opened = "Updated the request that was already open" if row["duplicate"] else "Created a new request"
        return (
            f"{opened}. Reference ID: {row['ref_id']} (urgency {row['urgency']}). "
            f"Delivered to the mentor channel: {'yes' if delivered else 'saved to the mentor desk queue'}. "
            f"Now tell the learner the reference ID slowly character by character, say a human mentor will "
            f"review it during academy hours and reply within one working day, and do NOT promise an instant reply."
        )

    @function_tool
    async def check_escalation_status(self, context: RunContext, reference_id: str) -> str:
        """Check what happened to a mentor request the learner already raised.

        Args:
            reference_id: The reference they were given, e.g. "ESC-4F2A".
        """
        logger.info(f"Checking escalation status for {reference_id}.")
        row = escalations.get(reference_id)
        if not row:
            return f"No mentor request found with reference '{reference_id}'. Ask them to re-read the ID."

        return (
            f"Request {row['ref_id']} is currently '{row['status']}' (urgency {row['urgency']}), "
            f"raised on {row['created_at']} about: {row['what_happened']}. "
            f"Tell them the status honestly in one short sentence."
        )

    @function_tool
    async def transfer_to_pid_specialist(
        self, context: RunContext, learner_request: str
    ) -> Agent | str:
        """Hand the conversation to Kabir, the PID tuning specialist.

        Use this ONLY when the learner's problem is about PID gains or line-tracking
        stability: the robot zig-zags or wobbles on the line, oscillates, overshoots
        curves, corrects too slowly, sits off-centre, or they are asking what to set
        Kp, Ki or Kd to. The spoken "I am connecting you to our PID specialist"
        announcement is handled for you — just call this tool.

        Do NOT use this for anything else. IR sensor thresholds, wiring order, L298N
        or motor driver basics, duty cycle, quizzes, word definitions, saving memory,
        burning smells or any hands-on hardware fault all stay with YOU.

        Args:
            learner_request: What the learner just asked, in their own words, so Kabir
                does not make them explain the problem again.
        """
        if not specialists.needs_pid_coach(learner_request):
            logger.info(f"Handoff refused — no PID signal in: '{learner_request}'")
            return (
                "NOT_TRANSFERRED: that request has no PID or tuning symptom in it, so it is "
                "yours to answer. Handle it yourself now, and only transfer if they describe "
                "zig-zagging, wobbling, oscillation, overshoot, or ask about Kp, Ki or Kd."
            )

        try:
            coach = specialists.PIDCoach(main=self, learner_request=learner_request)
        except Exception as e:
            # A failed handoff must not become a dead end — Rishika keeps the learner.
            logger.exception(f"Could not start the PID specialist: {e}")
            return (
                "HANDOFF_FAILED: the PID specialist could not be reached. Apologise in one "
                "short sentence, tell the learner you will help with the tuning yourself, "
                "and continue: Kp first until it tracks but wobbles, then Kd to damp the "
                "wobble, then Ki only if it still sits off-centre."
            )

        logger.info(f"Handing off to the PID specialist: '{learner_request}'")
        if hasattr(context, "session") and context.session:
            try:
                await context.session.say(static_intents.HANDOFF_TO_PID_FILLER)
            except Exception as e:
                logger.warning(f"Failed to speak handoff announcement: {e}")

        # Returning the Agent alone (no message) switches agents without Rishika
        # speaking again — the announcement above already happened, and the coach's
        # on_enter introduces him.
        return coach

    @function_tool
    async def stop_calling_me(self, context: RunContext) -> str:
        """Register a do-not-call request and end the call. Invoke IMMEDIATELY when the student says
        "stop calling", "don't call again", "बंद करो", "मुझे कॉल मत करो", or otherwise asks to opt out
        of practice calls. Confirm out loud, then the call hangs up.
        """
        phone = self.dial_info.get("phone_number", "")
        if not phone:
            return "This is a web session, not a phone call, so there is nothing to opt out of."

        db_memory.add_opt_out(phone)
        self.opted_out = True
        logger.info(f"Opt-out recorded for {phone}; hanging up.")
        asyncio.create_task(_hangup())
        return f"Recorded the do-not-call request for {phone}. Confirm warmly that they will not be called again, then say goodbye."


async def _hangup() -> None:
    """Delete the room so the SIP leg drops instead of leaving the callee in silence."""
    ctx = get_job_context()
    session = _sessions.get(ctx.room.name)
    if session and session.current_speech:
        await session.current_speech.wait_for_playout()
    await ctx.delete_room()


# Room name -> live session, so _hangup can drain speech before dropping the leg.
_sessions: dict[str, AgentSession] = {}


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="Rishika")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Day 6: dispatch metadata carries the number to dial. Empty on web sessions.
    dial_info = json.loads(ctx.job.metadata) if ctx.job.metadata else {}
    phone_number = dial_info.get("phone_number")

    # Day 8: one analytics row per call, written when the job shuts down — which happens
    # on every exit path, including a dial that never connected.
    assistant = Assistant(dial_info=dial_info)
    started_at = datetime.now().isoformat(timespec="seconds")

    async def _record_outcome(reason: str) -> None:
        analytics.record_call(
            room=ctx.room.name,
            channel="phone" if phone_number else "web",
            started_at=started_at,
            turns=assistant.turns,
            exercises=assistant.exercises,
            escalation_ref=assistant.escalation_ref,
            opted_out=assistant.opted_out,
            dial_failed=assistant.dial_failed,
            learner=assistant.learner,
            language=assistant.language,
        )

    ctx.add_shutdown_callback(_record_outcome)

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
            stt=deepgram.STT(model="nova-3", language="multi"), # <- you have to set "multi" here to detect non-english transcripts
            llm=google.LLM(
                    model="gemini-3.5-flash-lite",
                ),
            tts=murf.TTS(
                    voice="Anisha", # make sure locale key is not hardcoded
                    style="Casual", # excited, upbeat delivery style
                    tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                    text_pacing=True
                ),
            turn_detection=MultilingualModel(),
            vad=ctx.proc.userdata["vad"],
            preemptive_generation=True,
        )
    '''
    session = AgentSession(
            # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
            # See all available models at https://docs.livekit.io/agents/models/stt/
            stt=deepgram.STT(model="nova-3", language='multi'),
            # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
            # See all available models at https://docs.livekit.io/agents/models/llm/
            llm=google.LLM(
                    model="gemini-3.5-flash-lite",
                ),
            # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
            # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
            tts=murf.TTS(
                    voice="Samar",
                    style="Conversation",
                    tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                    text_pacing=True
                ),
            # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
            # See mo                re at https://docs.livekit.io/agents/build/turns
            turn_detection=MultilingualModel(),
            vad=ctx.proc.userdata["vad"],
            # allow the LLM to generate a response while waiting for the end of turn
            # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
            preemptive_generation=True,
        )
'''
    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    @session.on("user_input_transcribed")
    def _on_user_transcript(ev):
        # Day 8: how many times the learner actually spoke. Only the count is kept.
        if getattr(ev, "is_final", False) and (ev.transcript or "").strip():
            assistant.turns += 1

    @session.on("user_speech_committed")
    def _on_user_speech(ev):
        # Skip the canned greeting on outbound — the disclosure already introduced us.
        if phone_number:
            return
        text = getattr(ev, "content", None) or getattr(ev, "text", None) or ""
        if isinstance(text, str) and text.strip():
            matched = static_intents.match_static_intent(text)
            if matched:
                logger.info(f"Static intent interceptor matched: '{text}' -> {matched.intent_type}")
                asyncio.create_task(session.say(matched.text))

    # Join the room and connect to the user
    await ctx.connect()

    _sessions[ctx.room.name] = session

    # Day 6: on an outbound job, dial the learner and wait for a real answer before speaking.
    if phone_number:
        trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
        if not trunk_id:
            logger.error("SIP_OUTBOUND_TRUNK_ID is not set — cannot place outbound call.")
            assistant.dial_failed = True
            ctx.shutdown(reason="missing trunk")
            return

        try:
            await ctx.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    room_name=ctx.room.name,
                    sip_trunk_id=trunk_id,
                    sip_call_to=phone_number,
                    participant_identity=phone_number,
                    participant_name=dial_info.get("student_name") or "LFR Student",
                    wait_until_answered=True,
                    ringing_timeout=timedelta(seconds=30),
                    max_call_duration=timedelta(minutes=10),
                )
            )
        except api.TwirpError as e:
            # No answer / busy / rejected / trunk failure all surface here. Nothing to retry
            # inline — the dispatch script owns retry policy.
            logger.warning(
                f"Outbound call to {phone_number} failed: code={e.code} "
                f"sip_status={e.metadata.get('sip_status_code')} {e.metadata.get('sip_status')}"
            )
            assistant.dial_failed = True
            ctx.shutdown(reason=f"dial failed: {e.code}")
            return

        try:
            await ctx.wait_for_participant(identity=phone_number)
        except Exception as e:
            logger.warning(f"Callee never joined the room: {e}")
            assistant.dial_failed = True
            ctx.shutdown(reason="callee absent")
            return

        @ctx.room.on("participant_disconnected")
        def _on_disconnect(participant: rtc.RemoteParticipant):
            if participant.identity == phone_number:
                logger.info(f"{phone_number} hung up (reason={participant.disconnect_reason}).")

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Say the disclosure verbatim via TTS so the LLM cannot paraphrase away the opt-out line.
    if phone_number:
        await session.say(
            static_intents.outbound_opening(
                student_name=dial_info.get("student_name", ""),
                last_topic=dial_info.get("last_topic", ""),
            )
        )


if __name__ == "__main__":
    cli.run_app(server)
