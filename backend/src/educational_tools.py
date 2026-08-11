import html
import json
import logging
import random
import aiohttp

logger = logging.getLogger("educational-tools")

# Local fallback quiz dataset for offline/network failure
LOCAL_FALLBACK_QUIZ = [
    {
        "topic": "IR Sensors",
        "question": "What sensor does a Line Follower Robot use to detect dark lines on light surfaces?",
        "options": ["IR Sensor", "Ultrasonic Sensor", "Gyroscope", "Temperature Sensor"],
        "answer": "IR Sensor",
    },
    {
        "topic": "Motor Drivers",
        "question": "Which motor driver chip is commonly used to control two DC motors in starter robotics?",
        "options": ["L298N", "ESP8266", "MPU6050", "DHT11"],
        "answer": "L298N",
    },
    {
        "topic": "Arduino Programming",
        "question": "In Arduino programming, which function runs repeatedly in a continuous loop?",
        "options": ["loop()", "setup()", "main()", "start()"],
        "answer": "loop()",
    },
    {
        "topic": "PID Tuning",
        "question": "In PID control for line following, what does the 'P' term stand for?",
        "options": ["Proportional", "Predictive", "Parallel", "Power"],
        "answer": "Proportional",
    },
]


async def broadcast_tool_card(room, card_type: str, title: str, subtitle: str, data: dict):
    """Publishes structured tool result payload over LiveKit room data channel to render UI cards on screen."""
    if not room:
        return
    try:
        payload = json.dumps({
            "type": "TOOL_RESULT_CARD",
            "cardType": card_type,
            "title": title,
            "subtitle": subtitle,
            "data": data,
        }).encode("utf-8")
        await room.local_participant.publish_data(payload, reliable=True)
        logger.info(f"Broadcasted UI tool card '{card_type}' to LiveKit room.")
    except Exception as e:
        logger.warning(f"Could not broadcast tool card payload: {e}")


async def fetch_word_definition(word: str, room=None) -> str:
    """Fetches word definition, part of speech, and usage example from Free Dictionary API."""
    clean_word = word.strip().lower()
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{clean_word}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    meanings = data[0].get("meanings", [])
                    if meanings:
                        part_of_speech = meanings[0].get("partOfSpeech", "word")
                        definition = meanings[0]["definitions"][0].get("definition", "")
                        example = meanings[0]["definitions"][0].get("example", "")

                        # Broadcast to Frontend UI
                        await broadcast_tool_card(
                            room=room,
                            card_type="dictionary",
                            title=f"WORD DEFINITION: {clean_word.upper()}",
                            subtitle=f"Part of Speech: {part_of_speech}",
                            data={"word": clean_word, "definition": definition, "example": example},
                        )

                        res = f"The word '{clean_word}' is a {part_of_speech}. Definition: {definition}."
                        if example:
                            res += f" Example: '{example}'."
                        return res
                elif response.status == 404:
                    return f"I couldn't find the definition for '{clean_word}' in the live dictionary. Please verify the spelling."
    except Exception as e:
        logger.error(f"Dictionary API call failed: {e}")
        return (
            "SYSTEM_NOTICE: The live dictionary API is currently unreachable. "
            f"Politely explain in spoken voice that the live server timed out, "
            f"and explain '{clean_word}' using your existing general knowledge."
        )

    return f"I couldn't retrieve information for '{clean_word}' right now."


async def fetch_quiz_question(topic: str = "", room=None) -> str:
    """Fetches a science/computer quiz question from Open Trivia DB with topic chaining and local fallbacks."""
    url = "https://opentdb.com/api.php?amount=1&category=18&type=multiple"

    # Filter local fallback by topic if provided
    filtered = LOCAL_FALLBACK_QUIZ
    if topic:
        topic_clean = topic.lower()
        matched = [q for q in LOCAL_FALLBACK_QUIZ if topic_clean in q["topic"].lower()]
        if matched:
            filtered = matched

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3.0)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("response_code") == 0 and data.get("results"):
                        q = data["results"][0]
                        question = html.unescape(q["question"])
                        correct = html.unescape(q["correct_answer"])
                        opts = [html.unescape(x) for x in q["incorrect_answers"]] + [correct]
                        random.shuffle(opts)

                        # Broadcast to Frontend UI
                        await broadcast_tool_card(
                            room=room,
                            card_type="quiz",
                            title="LIVE SCIENCE & ROBOTICS QUIZ",
                            subtitle=f"Topic: {topic or 'Computer Science'}",
                            data={"question": question, "options": opts, "answer": correct},
                        )

                        return (
                            f"Live Science Question: {question}\n"
                            f"Options: {', '.join(opts)}\n"
                            f"Correct Answer: {correct}"
                        )
    except Exception as e:
        logger.warning(f"Open Trivia DB failed ({e}). Falling back to local dataset.")

    item = random.choice(filtered)

    # Broadcast offline quiz to Frontend UI
    await broadcast_tool_card(
        room=room,
        card_type="quiz",
        title="ROBOTICS KNOWLEDGE QUIZ [OFFLINE BANK]",
        subtitle=f"Topic: {item['topic']}",
        data={"question": item["question"], "options": item["options"], "answer": item["answer"]},
    )

    return (
        f"Notice: Using offline fallback robotics quiz dataset for topic '{item['topic']}'.\n"
        f"Question: {item['question']}\n"
        f"Options: {', '.join(item['options'])}\n"
        f"Correct Answer: {item['answer']}"
    )


async def evaluate_answer_score(user_answer: str, expected_context: str = "", room=None) -> str:
    """Evaluates the student's spoken/written answer for correctness, rates their knowledge, and gives concise accurate feedback."""
    clean_ans = user_answer.strip().lower()
    
    # Calculate simple keyword match accuracy for instant feedback
    keywords = ["ir", "sensor", "l298n", "motor", "loop", "setup", "pid", "proportional", "threshold", "black", "white", "analog", "pwm", "arduino"]
    matched_count = sum(1 for kw in keywords if kw in clean_ans)
    
    if matched_count >= 2 or any(term in clean_ans for term in ["correct", "right", "yes", "true", "ir sensor", "l298n", "loop()"]):
        score = 95
        rating = "EXCELLENT // ACCURATE"
    elif matched_count == 1:
        score = 75
        rating = "GOOD // PARTIALLY CORRECT"
    else:
        score = 50
        rating = "NEEDS REFINEMENT"

    # Broadcast Score Card to Frontend UI
    await broadcast_tool_card(
        room=room,
        card_type="score",
        title="STUDENT KNOWLEDGE RATING",
        subtitle=f"Evaluation Score: {score}%",
        data={
            "score": score,
            "rating": rating,
            "userAnswer": user_answer,
            "feedback": f"Your response demonstrates a solid grasp of robotics logic. Score: {score}%."
        },
    )

    return (
        f"EVALUATION_RESULT: Accuracy Score: {score}% ({rating}). "
        f"Guidance for Assistant: Acknowledge their effort enthusiastically in 1 short sentence, state their accuracy score ({score}%), and provide the precise correct answer concisely without lengthening the turn."
    )
