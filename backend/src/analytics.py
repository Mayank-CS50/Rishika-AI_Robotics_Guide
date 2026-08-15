"""Day 8 — did the call actually work?

Success for the Learning & Literacy track means the learner completed an exercise:
Rishika scored at least one spoken answer with `score_spoken_answer`. A call that
correctly handed the learner to a human mentor (Day 7) also reached its goal, so it
counts too. Everything else is a failure — not a crash, just a call that never got
there: nobody spoke, they left before finishing, they opted out, or the phone never
connected.

One row per room, written once when the job shuts down, for browser and SIP calls
alike. Only counters and outcomes are stored: no transcript, no phone number, no
OTP — nothing a dashboard should not show.

The page is served by escalations.py (one server, one port); this module owns the
table, the numbers and the markup.

    uv run python src/analytics.py      # print the numbers
"""

import html
import logging
import sys
from contextlib import suppress
from datetime import datetime

from db_memory import get_connection

logger = logging.getLogger("analytics")

# Why a call ended where it did. The first two are the success conditions.
OUTCOME_REASONS = {
    "exercise_completed": "Completed an exercise",
    "escalated": "Handed to a human mentor",
    "no_engagement": "Nobody spoke",
    "left_early": "Left before finishing an exercise",
    "opted_out": "Asked to stop the practice calls",
    "not_connected": "Never connected (no answer, busy, or trunk error)",
}


def _init():
    """Create the calls table if it does not exist yet. No transcript column — by design."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS calls (
                room TEXT PRIMARY KEY,
                channel TEXT DEFAULT 'web',
                learner TEXT DEFAULT '',
                language TEXT DEFAULT '',
                turns INTEGER DEFAULT 0,
                exercises INTEGER DEFAULT 0,
                escalation_ref TEXT DEFAULT '',
                outcome TEXT NOT NULL,
                outcome_reason TEXT NOT NULL,
                started_at TIMESTAMP,
                ended_at TIMESTAMP,
                duration_s INTEGER DEFAULT 0
            )
            """
        )


def classify(
    turns: int = 0,
    exercises: int = 0,
    escalation_ref: str = "",
    opted_out: bool = False,
    dial_failed: bool = False,
) -> tuple[str, str]:
    """Decide success/failed from what actually happened in the call.

    Checked in order of how much the learner got out of it: a scored exercise wins
    even if they hung up angry afterwards.
    """
    if dial_failed:
        return "failed", "not_connected"
    if exercises:
        return "success", "exercise_completed"
    if escalation_ref:
        return "success", "escalated"
    if opted_out:
        return "failed", "opted_out"
    if not turns:
        return "failed", "no_engagement"
    return "failed", "left_early"


def _safe_name(name: str) -> str:
    """Letters only — a dashboard never needs digits, and digits are how PII sneaks in."""
    return "".join(c for c in (name or "") if c.isalpha() or c.isspace()).strip()[:24]


def record_call(
    room: str,
    channel: str = "web",
    started_at: str = "",
    turns: int = 0,
    exercises: int = 0,
    escalation_ref: str = "",
    opted_out: bool = False,
    dial_failed: bool = False,
    learner: str = "",
    language: str = "",
) -> dict:
    """Write this call's outcome. Keyed on room, so a reconnect updates instead of double counting."""
    outcome, reason = classify(turns, exercises, escalation_ref, opted_out, dial_failed)
    ended = datetime.now()
    started = ended
    if started_at:
        with suppress(ValueError):
            started = datetime.fromisoformat(started_at)
    duration = max(0, int((ended - started).total_seconds()))

    _init()
    row = {
        "room": room,
        "channel": "phone" if channel == "phone" else "web",
        "learner": _safe_name(learner),
        "language": _safe_name(language),
        "turns": turns,
        "exercises": exercises,
        "escalation_ref": escalation_ref or "",
        "outcome": outcome,
        "outcome_reason": reason,
        "started_at": started.isoformat(timespec="seconds"),
        "ended_at": ended.isoformat(timespec="seconds"),
        "duration_s": duration,
    }
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO calls (room, channel, learner, language, turns, exercises, escalation_ref,
                               outcome, outcome_reason, started_at, ended_at, duration_s)
            VALUES (:room, :channel, :learner, :language, :turns, :exercises, :escalation_ref,
                    :outcome, :outcome_reason, :started_at, :ended_at, :duration_s)
            ON CONFLICT(room) DO UPDATE SET
                turns = excluded.turns,
                exercises = excluded.exercises,
                escalation_ref = excluded.escalation_ref,
                outcome = excluded.outcome,
                outcome_reason = excluded.outcome_reason,
                ended_at = excluded.ended_at,
                duration_s = excluded.duration_s
            """,
            row,
        )
    logger.info(f"Call {room} recorded as {outcome} ({reason}) after {duration}s.")
    return row


def stats() -> dict:
    """The three numbers the dashboard must show, plus the success rate and the why."""
    _init()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT outcome, outcome_reason, COUNT(*) AS n FROM calls GROUP BY outcome, outcome_reason"
        ).fetchall()

    total = sum(r["n"] for r in rows)
    success = sum(r["n"] for r in rows if r["outcome"] == "success")
    return {
        "total": total,
        "success": success,
        "failed": total - success,
        "rate": round(success * 100 / total) if total else 0,
        "breakdown": sorted(
            (
                {
                    "label": OUTCOME_REASONS.get(r["outcome_reason"], r["outcome_reason"]),
                    "count": r["n"],
                    "outcome": r["outcome"],
                }
                for r in rows
            ),
            key=lambda d: -d["count"],
        ),
    }


def recent(limit: int = 12) -> list[dict]:
    """Latest calls for the history table. Learner first names at most."""
    _init()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM calls ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def _clock(seconds: int) -> str:
    return f"{seconds // 60}m {seconds % 60:02d}s"


def render_html() -> str:
    """The dashboard section of the ops page. Styling lives in escalations._PAGE."""
    s = stats()
    kpis = "".join(
        f'<div class="kpi {cls}"><b>{value}</b><span>{label}</span></div>'
        for value, label, cls in (
            (s["total"], "Total calls", ""),
            (s["success"], "Successful", "ok"),
            (s["failed"], "Failed", "bad"),
            (f"{s['rate']}%", "Success rate", ""),
        )
    )
    breakdown = "".join(
        f'<li class="{html.escape(b["outcome"])}">{html.escape(b["label"])}'
        f'<b>{b["count"]}</b></li>'
        for b in s["breakdown"]
    ) or "<li>No calls yet — start a session and hang up.</li>"

    history = "".join(
        "<tr>"
        f'<td>{html.escape(r["started_at"][5:16].replace("T", " "))}</td>'
        f'<td>{html.escape(r["channel"])}</td>'
        f'<td>{html.escape(r["learner"] or "—")}</td>'
        f'<td>{_clock(r["duration_s"])}</td>'
        f'<td>{r["turns"]}</td>'
        f'<td>{r["exercises"]}</td>'
        f'<td class="{html.escape(r["outcome"])}">{html.escape(r["outcome"].upper())} · '
        f'{html.escape(OUTCOME_REASONS.get(r["outcome_reason"], r["outcome_reason"]))}</td>'
        "</tr>"
        for r in recent()
    )

    return (
        f'<h1>CALL ANALYTICS</h1><div class="kpis">{kpis}</div>'
        f'<ul class="reasons">{breakdown}</ul>'
        f'<table><tr><th>Started<th>Channel<th>Learner<th>Duration<th>Turns'
        f"<th>Exercises<th>Outcome{history}</table>"
    )


def main() -> int:
    s = stats()
    print(
        f"total {s['total']} · successful {s['success']} · failed {s['failed']} "
        f"· success rate {s['rate']}%\n"
    )
    for b in s["breakdown"]:
        print(f"  {b['count']:>3}  {b['label']}")
    print()
    for r in recent():
        print(
            f"  {r['started_at'][5:16]}  {r['channel']:<5} {r['learner'] or '—':<12} "
            f"{_clock(r['duration_s']):>7}  {r['outcome']:<7} {r['outcome_reason']}"
        )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main())
