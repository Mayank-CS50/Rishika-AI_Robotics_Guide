from static_intents import match_static_intent


def test_greeting_matches():
    greetings = ["hi", "Hello!", "namaste", "नमस्ते", "नमस्कार"]
    for g in greetings:
        match = match_static_intent(g)
        assert match is not None, f"Failed to match greeting: {g}"
        assert match.intent_type == "greeting"


def test_farewell_matches():
    farewells = ["bye", "Goodbye", "bye bye", "अलविदा", "फिर मिलेंगे"]
    for f in farewells:
        match = match_static_intent(f)
        assert match is not None, f"Failed to match farewell: {f}"
        assert match.intent_type == "farewell"


def test_complex_query_does_not_match():
    queries = [
        "Hi, my name is Ramesh and my LFR robot IR sensor is not calibrating",
        "How do I tune PID parameters for line follower?",
        "नमस्ते Rishika, I want to learn motor driver circuit",
    ]
    for q in queries:
        match = match_static_intent(q)
        assert match is None, f"Complex query incorrectly matched static intent: {q}"
