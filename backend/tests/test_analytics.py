"""Day 8 call analytics checks — no network, no LiveKit, no LLM required.

Covers the success path the task asks for (learner completed an exercise), the
failure paths, and the rule that nothing private ever reaches the dashboard.
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import analytics
import db_memory


def _isolate(monkeypatch, tmp):
    monkeypatch.setattr(db_memory, "DB_DIR", tmp)
    monkeypatch.setattr(db_memory, "DB_PATH", os.path.join(tmp, "t.db"))


def test_success_condition_is_a_completed_exercise():
    """Step 1: success = the learner finished an exercise, or was handed to a human."""
    assert analytics.classify(turns=6, exercises=1) == ("success", "exercise_completed")
    assert analytics.classify(turns=4, escalation_ref="ESC-1234") == ("success", "escalated")
    # An exercise still counts even if they opted out right afterwards.
    assert analytics.classify(turns=9, exercises=2, opted_out=True)[0] == "success"


def test_failures_say_why_without_pretending_something_broke():
    """Step 2: a failed call is one that missed the goal, not necessarily an error."""
    assert analytics.classify() == ("failed", "no_engagement")
    assert analytics.classify(turns=5) == ("failed", "left_early")
    assert analytics.classify(turns=2, opted_out=True) == ("failed", "opted_out")
    assert analytics.classify(dial_failed=True) == ("failed", "not_connected")


def test_dashboard_numbers_come_from_recorded_calls(monkeypatch):
    """Steps 3 & 4: total / successful / failed are counted, never hardcoded."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        assert analytics.stats() == {
            "total": 0, "success": 0, "failed": 0, "rate": 0, "breakdown": [],
        }, "an empty database must show zeros, not placeholders"

        analytics.record_call(room="web-1", exercises=1, turns=8, learner="Ramesh")
        analytics.record_call(room="web-2", turns=3)
        analytics.record_call(room="phone-1", channel="phone", dial_failed=True)
        analytics.record_call(room="web-3", turns=5, escalation_ref="ESC-9AB1")

        s = analytics.stats()
        assert (s["total"], s["success"], s["failed"], s["rate"]) == (4, 2, 2, 50)
        assert sum(b["count"] for b in s["breakdown"]) == 4

        html = analytics.render_html()
        for expected in ("Total calls", "Success rate", "50%", "Ramesh", "phone"):
            assert expected in html


def test_a_reconnect_updates_the_call_instead_of_counting_it_twice(monkeypatch):
    """Real sessions drop and rejoin — one room must stay one call."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        analytics.record_call(room="web-1", turns=2)
        analytics.record_call(room="web-1", turns=7, exercises=1)

        s = analytics.stats()
        assert (s["total"], s["success"]) == (1, 1), "the later outcome wins"
        assert analytics.recent()[0]["turns"] == 7


def test_duration_is_measured_not_guessed(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        started = (datetime.now() - timedelta(seconds=95)).isoformat(timespec="seconds")
        row = analytics.record_call(room="web-1", started_at=started, turns=4, exercises=1)
        assert 90 <= row["duration_s"] <= 105
        assert "1m 3" in analytics._clock(95)


def test_nothing_private_can_reach_the_dashboard(monkeypatch):
    """Step 6: no transcripts, no phone numbers, no OTPs — enforced by the schema."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        analytics.record_call(
            room="phone-1",
            channel="phone",
            turns=4,
            exercises=1,
            learner="Ramesh 9876543210",  # a hallucinated name carrying a number
        )

        row = analytics.recent()[0]
        assert row["learner"] == "Ramesh", "digits must never survive into the dashboard"

        columns = set(row)
        assert not columns & {"transcript", "phone", "phone_number", "messages", "audio"}

        blob = analytics.render_html() + str(row)
        assert "9876543210" not in blob
