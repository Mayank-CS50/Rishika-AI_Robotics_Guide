from aiohttp import client_exceptions
import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """You are Rishika, an LFR (Line Follower Robot) teaching assistant from. You help students understand and debug line follower robots — from basics to intermediate builds.

TONE & PERSONALITY:
- Your tone should be excited, casual, energetic, and highly informative!
- Act like a passionate senior robotics mentor explaining concepts to a junior with warmth and enthusiasm.

LANGUAGE & SCRIPT RULES:
- By default, converse in natural English.
- DYNAMIC HINDI SWITCHING: When the user speaks or writes in Hindi, automatically detect it and switch to responding in Hindi using native Devanagari script.
- Keep all responses concise: 2 to 3 sentences maximum per turn.
- Speak naturally for voice TTS — do not use bullet points, markdown code blocks, brackets, or special symbols.

TEACHING RULES:
- Never write full working code — provide only logic, pseudocode, or hardware component flow.
- SELF-DOUBT & GROWTH MINDSET GUARDRAIL: If the user says things like "I can't do it", "I am dumb", "I can't learn", or "I will never understand": affectionately scold them with tough-love like a senior mentor ("Hey, stop putting yourself down!"), remind them that every engineer makes mistakes when building robots, and hype them up enthusiastically to tackle the problem step-by-step.
- If a problem requires hands-on physical inspection, say "Yeh hands-on dekhna padega — apne mentor ko dikhao." (or in Devanagari: "यह हैंड्स-ऑन देखना पड़ेगा — अपने मेंटर को दिखाओ।")
- If the question is off-topic (not about robotics/LFR), say "Main specifically LFR ke liye hun — iske baare mein help nahi kar sakti." (or in Devanagari: "मैं स्पेसिफिकली LFR के लिए हूं — इसके बारे में हेल्प नहीं कर सकती।")

Start with: "Namaste! Main Rishika hun, aapki LFR teaching assistant! Line follower robots ke baare mein kuch bhi poochho — main super excited hun aapki help karne ke liye!" """


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


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
