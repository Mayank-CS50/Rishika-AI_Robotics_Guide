"""Day 7 human-handoff checks — no network, no LiveKit, no LLM required.

Covers both paths the task asks for: a conversation that needs a human creates exactly
one request, and everything else (no consent, normal lesson) creates nothing.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import db_memory
import escalations


def _isolate(monkeypatch, tmp):
    monkeypatch.setattr(db_memory, "DB_DIR", tmp)
    monkeypatch.setattr(db_memory, "DB_PATH", os.path.join(tmp, "t.db"))


def test_no_consent_creates_nothing(monkeypatch):
    """Step 4: if the learner says no, the request must not exist anywhere."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        assert escalations.create_or_update(
            learner_name="Ramesh",
            reason="learner_distress",
            what_happened="Wants to quit the course.",
            consent_confirmed=False,
        ) is None
        assert escalations.list_open() == [], "a refused handoff must leave no trace"


def test_normal_lesson_leaves_the_queue_empty(monkeypatch):
    """Step 7: an ordinary conversation never touches the escalation queue."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        db_memory.save_user(user_id="Priya", name="Priya", topics_covered="IR thresholds")
        assert escalations.list_open() == []


def test_consented_handoff_is_created_with_a_reference_id(monkeypatch):
    """Step 6: the learner must get an ID they can read back later."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        row = escalations.create_or_update(
            learner_name="Ramesh",
            reason="needs_human_mentor",
            what_happened="L298N is getting hot and smells burnt.",
            already_checked="Wiring order and IR threshold values.",
            urgency="high",
            language="Hindi",
            follow_up="call back",
            consent_confirmed=True,
        )

        assert row["ref_id"].startswith("ESC-")
        assert row["status"] == "open"
        assert row["duplicate"] is False
        assert escalations.get(row["ref_id"].lower())["learner"] == "Ramesh", "IDs are read back by voice"
        assert len(escalations.list_open()) == 1

        summary = escalations.format_summary(row)
        for expected in ("Ramesh", "Hindi", "high".upper(), "Wiring order", "call back"):
            assert expected in summary


def test_private_details_are_stripped(monkeypatch):
    """Step 3: no OTPs, PINs or phone numbers may reach the mentor — but robotics terms survive."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        row = escalations.create_or_update(
            learner_name="Ramesh",
            reason="learner_distress",
            what_happened="Call me on 9876543210, my OTP is 448122 and the PID loop keeps failing.",
            already_checked="L298N pins and the 5V rail.",
            consent_confirmed=True,
        )

        blob = escalations.format_summary(row)
        assert "9876543210" not in blob
        assert "448122" not in blob
        assert "[redacted]" in blob
        assert "PID" in blob, "over-redaction must not eat the actual problem"
        assert "L298N" in blob, "part numbers are not secrets"


def test_repeat_escalation_updates_instead_of_duplicating(monkeypatch):
    """Advanced: the mentor should see one request per problem, not five."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        first = escalations.create_or_update(
            learner_name="Ramesh",
            reason="needs_human_mentor",
            what_happened="Motor driver heating up.",
            urgency="medium",
            consent_confirmed=True,
        )
        second = escalations.create_or_update(
            learner_name="ramesh",  # same human, different casing
            reason="needs_human_mentor",
            what_happened="Motor driver now smells burnt.",
            urgency="emergency",
            consent_confirmed=True,
        )

        assert second["ref_id"] == first["ref_id"]
        assert second["duplicate"] is True
        assert second["urgency"] == "emergency", "the update must carry the worse news"
        assert second["created_at"] == first["created_at"], "raised-at is when it first came in"
        assert len(escalations.list_open()) == 1

        # A different problem for the same learner is a separate request.
        other = escalations.create_or_update(
            learner_name="Ramesh",
            reason="learner_distress",
            what_happened="Says he is giving up.",
            consent_confirmed=True,
        )
        assert other["ref_id"] != first["ref_id"]
        assert len(escalations.list_open()) == 2


def test_resolved_requests_leave_the_open_queue(monkeypatch):
    """Advanced: status must be real, so the agent can answer 'what happened to my request?'."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        row = escalations.create_or_update(
            learner_name="Priya",
            reason="learner_distress",
            what_happened="Upset after the robot failed in class.",
            consent_confirmed=True,
        )

        assert escalations.set_status(row["ref_id"], "in_progress")
        assert escalations.list_open()[0]["status"] == "in_progress"

        assert escalations.set_status(row["ref_id"], "resolved")
        assert escalations.list_open() == []
        assert escalations.get(row["ref_id"])["status"] == "resolved"
        assert not escalations.set_status("ESC-NOPE", "resolved")


def test_bad_inputs_fall_back_instead_of_dropping_the_request(monkeypatch):
    """A hallucinated reason or urgency must not lose a learner who needs help."""
    with tempfile.TemporaryDirectory() as tmp:
        _isolate(monkeypatch, tmp)

        row = escalations.create_or_update(
            learner_name="Ramesh",
            reason="robot_on_fire",
            what_happened="Wheels dead after rewiring.",
            urgency="catastrophic",
            consent_confirmed=True,
        )

        assert row["reason"] == "needs_human_mentor"
        assert row["urgency"] == "medium"
        assert len(escalations.list_open()) == 1
