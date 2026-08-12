"""Day 6 outbound call checks — no network, no LiveKit, no phone required."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import db_memory
import static_intents


def test_opt_out_roundtrip(monkeypatch):
    """Opt-out must persist and must survive formatting differences in the number."""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(db_memory, "DB_DIR", tmp)
        monkeypatch.setattr(db_memory, "DB_PATH", os.path.join(tmp, "t.db"))

        assert not db_memory.is_opted_out("+919876543210")

        db_memory.add_opt_out("+91 98765-43210")
        # Same human, different formatting — must still be blocked.
        assert db_memory.is_opted_out("+919876543210")
        assert db_memory.is_opted_out("+91 98765 43210")
        # An unrelated number must not be swept up.
        assert not db_memory.is_opted_out("+919999999999")


def test_opt_out_handles_sip_usernames(monkeypatch):
    """A SIP target must not be digit-stripped into a collision with another user."""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(db_memory, "DB_DIR", tmp)
        monkeypatch.setattr(db_memory, "DB_PATH", os.path.join(tmp, "t.db"))

        db_memory.add_opt_out("Mayank123")
        assert db_memory.is_opted_out("mayank123"), "SIP usernames are case-insensitive"
        assert not db_memory.is_opted_out("+123"), "must not collapse to its digits"
        assert not db_memory.is_opted_out("ramesh123")


def test_opt_out_can_be_cleared(monkeypatch):
    """Re-dialing after demoing 'stop calling' must be possible, and must be explicit."""
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(db_memory, "DB_DIR", tmp)
        monkeypatch.setattr(db_memory, "DB_PATH", os.path.join(tmp, "t.db"))

        db_memory.add_opt_out("+919876543210")
        assert db_memory.remove_opt_out("+91 98765-43210"), "same human, different formatting"
        assert not db_memory.is_opted_out("+919876543210")
        assert not db_memory.remove_opt_out("+919876543210"), "second clear is a no-op"


def test_opening_states_who_why_and_optout():
    """Day 6 hard requirement: identity, reason, and opt-out in the opening."""
    opening = static_intents.outbound_opening(student_name="Ramesh", last_topic="PID ट्यूनिंग")

    assert "ऋषिका" in opening, "must say who is calling"
    assert "Firefly Academy" in opening, "must name the org"
    assert "Ramesh" in opening
    assert "PID ट्यूनिंग" in opening, "must say why we called"
    assert "स्टॉप कॉलिंग" in opening, "must say how to make it stop"


def test_opening_without_saved_profile():
    """A first-time learner still gets a complete disclosure."""
    opening = static_intents.outbound_opening()

    assert "ऋषिका" in opening
    assert "स्टॉप कॉलिंग" in opening
    assert "None" not in opening, "empty profile must not leak placeholder text"
