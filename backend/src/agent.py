from aiohttp import client_exceptions
import logging
import db_memory
import static_intents
import educational_tools

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    function_tool,
    cli,
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
- If a problem requires hands-on physical inspection, say: "यह हैंड्स-ऑन देखना पड़ेगा — अपने मेंटर को दिखाओ।"
- If the question is off-topic (not about robotics/LFR), say: "मैं स्पेसिफिकली LFR के लिए हूं — इसके बारे में हेल्प नहीं कर सकती।" """


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def lookup_user(self, context: RunContext, user_identifier: str) -> str:
        """Use this tool to look up a returning student's memory profile by their name or user ID.

        Args:
            user_identifier: The caller's name or user ID (e.g. "Ramesh", "Priya", "user_101").
        """
        logger.info(f"Looking up memory record for {user_identifier}.")
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
        room = getattr(context, "room", None)
        return await educational_tools.evaluate_answer_score(user_answer, question_or_topic, room=room)



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

    @session.on("user_speech_committed")
    def _on_user_speech(ev):
        text = getattr(ev, "content", None) or getattr(ev, "text", None) or ""
        if isinstance(text, str) and text.strip():
            matched = static_intents.match_static_intent(text)
            if matched:
                logger.info(f"Static intent interceptor matched: '{text}' -> {matched.intent_type}")
                import asyncio
                asyncio.create_task(session.say(matched.text))

    # Join the room and connect to the user
    await ctx.connect()


    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
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


if __name__ == "__main__":
    cli.run_app(server)
