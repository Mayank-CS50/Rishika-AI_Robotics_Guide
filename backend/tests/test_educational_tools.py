import pytest
from educational_tools import fetch_word_definition, fetch_quiz_question


@pytest.mark.asyncio
async def test_lookup_valid_word():
    result = await fetch_word_definition("sensor")
    assert "sensor" in result.lower()
    assert "definition:" in result.lower() or "is a" in result.lower()


@pytest.mark.asyncio
async def test_lookup_invalid_word():
    result = await fetch_word_definition("xyzabc12345nonexistentword")
    assert "couldn't find" in result.lower() or "verify the spelling" in result.lower()


@pytest.mark.asyncio
async def test_fetch_quiz_question():
    result = await fetch_quiz_question()
    assert "Question:" in result or "Live Science Question:" in result
    assert "Options:" in result
    assert "Correct Answer:" in result
