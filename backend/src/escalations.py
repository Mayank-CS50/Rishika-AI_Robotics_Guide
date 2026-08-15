"""Day 7 — hand the learner off to a real human mentor.

Rishika escalates in exactly two situations. She already recognises both in her
prompt; until now she had no action to take beyond saying "show your mentor":

    learner_distress    the learner is upset, quitting, or stuck in self-doubt
    needs_human_mentor  the fault needs hands-on hardware inspection

The request is written to the same SQLite file as student memory, so the desk page
below always works with zero credentials. If ESCALATION_WEBHOOK_URL is set, the
summary is also POSTed to Discord/Slack.

    uv run python src/escalations.py                  # ops page, http://127.0.0.1:8787
    uv run python src/escalations.py --list
    uv run python src/escalations.py --resolve ESC-4F2A

The same page also renders the Day 8 call analytics (see analytics.py), so one
command shows both how the agent is performing and what needs a human.

The page is read-only and binds to 127.0.0.1 only, so it has no auth. Do not
port-forward it or bind it to 0.0.0.0 — learner names and problems are on it.
"""

import argparse
import html
import logging
import os
import re
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from uuid import uuid4

import aiohttp

import analytics
from db_memory import get_connection

logger = logging.getLogger("escalations")

# The only two reasons Rishika is allowed to escalate for.
REASONS = {
    "learner_distress": "Learner is upset and needs a human teacher",
    "needs_human_mentor": "Hands-on hardware check — cannot be done over voice",
}
URGENCIES = ("low", "medium", "high", "emergency")
DESK_PORT = int(os.getenv("ESCALATION_DESK_PORT", "8787"))


def _init():
    """Create the escalations table if it does not exist yet."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                ref_id TEXT PRIMARY KEY,
                learner TEXT NOT NULL,
                reason TEXT NOT NULL,
                what_happened TEXT NOT NULL,
                already_checked TEXT DEFAULT '',
                urgency TEXT DEFAULT 'medium',
                language TEXT DEFAULT 'Hindi',
                follow_up TEXT DEFAULT '',
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
            """
        )


# Anything shaped like a phone / account / OTP number, plus whatever follows a
# secret-ish keyword. Over-redacting a summary is free; leaking a PIN is not.
_DIGIT_RUN = re.compile(r"\b\d[\d\s-]{3,}\d\b")
_SECRET_WORD = re.compile(
    r"(?i)\b(otp|pin|passcode|password|cvv|aadhaar|upi|card|account(?:\s*number)?)\b[:\s]*\S*"
)


def scrub(text: str) -> str:
    """Strip numbers and secrets out of a field before it ever leaves this process."""
    if not text:
        return ""
    cleaned = _SECRET_WORD.sub(lambda m: f"{m.group(1)} [redacted]", text)
    return _DIGIT_RUN.sub("[redacted]", cleaned).strip()


def create_or_update(
    learner_name: str,
    reason: str,
    what_happened: str,
    already_checked: str = "",
    urgency: str = "medium",
    language: str = "Hindi",
    follow_up: str = "",
    consent_confirmed: bool = False,
) -> dict | None:
    """Write (or refresh) one human-help request. Returns None when consent was refused.

    Consent is enforced here and not only in the prompt: an LLM that forgets to ask
    must not be able to create a row. Re-escalating the same reason for the same
    learner updates the open request instead of spawning a duplicate.
    """
    if not consent_confirmed:
        logger.info("Escalation dropped — learner did not consent to sharing their details.")
        return None

    reason = reason if reason in REASONS else "needs_human_mentor"
    urgency = urgency.lower() if urgency.lower() in URGENCIES else "medium"
    learner = scrub(learner_name) or "Unknown learner"
    now = datetime.now().isoformat(timespec="seconds")

    _init()
    with get_connection() as conn:
        open_row = conn.execute(
            "SELECT ref_id, created_at FROM escalations "
            "WHERE LOWER(learner) = LOWER(?) AND reason = ? AND status != 'resolved'",
            (learner, reason),
        ).fetchone()
        ref_id = open_row["ref_id"] if open_row else "ESC-" + uuid4().hex[:4].upper()
        conn.execute(
            """
            INSERT INTO escalations (ref_id, learner, reason, what_happened, already_checked,
                                     urgency, language, follow_up, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
            ON CONFLICT(ref_id) DO UPDATE SET
                what_happened = excluded.what_happened,
                already_checked = excluded.already_checked,
                urgency = excluded.urgency,
                language = excluded.language,
                follow_up = excluded.follow_up,
                updated_at = excluded.updated_at
            """,
            (
                ref_id,
                learner,
                reason,
                scrub(what_happened),
                scrub(already_checked),
                urgency,
                language,
                scrub(follow_up),
                open_row["created_at"] if open_row else now,
                now,
            ),
        )

    logger.info(f"{'Updated' if open_row else 'Raised'} escalation {ref_id} for {learner} ({urgency}).")
    row = get(ref_id) or {}
    row["duplicate"] = open_row is not None
    return row


def get(ref_id: str) -> dict | None:
    """Fetch one request by its spoken reference ID (case/space tolerant)."""
    _init()
    clean = (ref_id or "").strip().upper().replace(" ", "")
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM escalations WHERE ref_id = ?", (clean,)).fetchone()
    return dict(row) if row else None


def list_open() -> list[dict]:
    """Every unresolved request, most urgent first — this is what the mentor desk shows."""
    _init()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM escalations WHERE status != 'resolved' "
            "ORDER BY CASE urgency WHEN 'emergency' THEN 0 WHEN 'high' THEN 1 "
            "WHEN 'medium' THEN 2 ELSE 3 END, created_at"
        ).fetchall()
    return [dict(r) for r in rows]


def set_status(ref_id: str, status: str) -> bool:
    """Move a request to open / in_progress / resolved. Used by the mentor, not the agent."""
    if status not in ("open", "in_progress", "resolved"):
        return False
    _init()
    clean = (ref_id or "").strip().upper()
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE escalations SET status = ?, updated_at = ? WHERE ref_id = ?",
            (status, datetime.now().isoformat(timespec="seconds"), clean),
        )
        return cursor.rowcount > 0


def format_summary(row: dict) -> str:
    """The short handoff note a human actually reads. Never the whole transcript."""
    return (
        f"{row['ref_id']} · {row['urgency'].upper()} · {row['status']}\n"
        f"Who needs help: {row['learner']} (speaking {row['language']})\n"
        f"Why a human: {REASONS.get(row['reason'], row['reason'])}\n"
        f"What happened: {row['what_happened']}\n"
        f"Rishika already checked: {row['already_checked'] or '—'}\n"
        f"Preferred follow-up: {row['follow_up'] or 'not stated'}\n"
        f"Raised: {row['created_at']}"
    )


async def notify(row: dict) -> bool:
    """POST the summary to a real inbox. A no-op — not an error — when unconfigured.

    Discord reads `content`, Slack reads `text`, and each ignores the other's key, so
    one payload covers both without sniffing the URL.
    """
    url = os.getenv("ESCALATION_WEBHOOK_URL", "").strip()
    if not url:
        return False

    body = f"🚨 Rishika needs a human mentor\n{format_summary(row)}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json={"content": body, "text": body},
                timeout=aiohttp.ClientTimeout(total=5.0),
            ) as response:
                if response.status < 300:
                    logger.info(f"Escalation {row['ref_id']} delivered to webhook.")
                    return True
                logger.warning(f"Escalation webhook returned HTTP {response.status}.")
    except Exception as e:
        logger.warning(f"Escalation webhook failed ({e}); the request is still in SQLite.")
    return False


_PAGE = """<!doctype html><meta charset="utf-8"><title>Rishika ops desk</title>
<meta http-equiv="refresh" content="10">
<style>
body{{background:#0c0a18;color:#e4e4e7;font:14px/1.7 ui-monospace,monospace;padding:2rem}}
h1{{color:#EC4899;font-size:.8rem;letter-spacing:.25em;margin:2rem 0 .5rem}}
article{{border:1px solid rgba(236,72,153,.6);border-radius:14px;padding:1rem 1.25rem;
margin:1rem 0;max-width:44rem;white-space:pre-wrap}}
article.high,article.emergency{{border-color:#ef4444;color:#fecaca}}
small{{color:#71717a}}
.kpis{{display:flex;gap:1rem;flex-wrap:wrap}}
.kpi{{border:1px solid rgba(236,72,153,.35);border-radius:14px;padding:1rem 1.5rem;min-width:9rem}}
.kpi b{{display:block;font-size:2rem;line-height:1.2}}
.kpi span{{color:#a1a1aa;font-size:.7rem;letter-spacing:.15em;text-transform:uppercase}}
.kpi.ok b{{color:#10B981}} .kpi.bad b{{color:#ef4444}}
.reasons{{list-style:none;padding:0;max-width:32rem}}
.reasons li{{display:flex;justify-content:space-between;border-bottom:1px dashed #27272a;padding:.2rem 0}}
.reasons li.success{{color:#10B981}} .reasons li.failed{{color:#f87171}}
table{{border-collapse:collapse;font-size:.75rem;margin-top:.5rem}}
th,td{{text-align:left;padding:.35rem .9rem .35rem 0;border-bottom:1px solid #1f1f27;white-space:nowrap}}
th{{color:#71717a;font-weight:400;text-transform:uppercase;letter-spacing:.1em}}
td.success{{color:#10B981}} td.failed{{color:#f87171}}
</style>
{analytics}
<h1>OPEN MENTOR REQUESTS ({count})</h1>
{body}
<small>Auto-refreshes every 10s · localhost only · no transcripts, numbers or secrets stored</small>"""


class _Desk(BaseHTTPRequestHandler):
    """Read-only page so the human can see the queue. GET is the whole API."""

    def do_GET(self):
        rows = list_open()
        body = "".join(
            f'<article class="{html.escape(r["urgency"])}">{html.escape(format_summary(r))}</article>'
            for r in rows
        ) or "<article>Nothing open — Rishika is handling her own lessons.</article>"
        page = _PAGE.format(
            count=len(rows), body=body, analytics=analytics.render_html()
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def log_message(self, *args):
        pass  # the 10s auto-refresh would flood the console


def main() -> int:
    p = argparse.ArgumentParser(description="Mentor desk for Rishika's human-help requests.")
    p.add_argument("--list", action="store_true", help="Print open requests and exit")
    p.add_argument("--resolve", metavar="REF", help="Mark a request resolved (e.g. ESC-4F2A)")
    p.add_argument("--start", metavar="REF", help="Mark a request in_progress")
    args = p.parse_args()

    if args.resolve or args.start:
        ref, status = (args.resolve, "resolved") if args.resolve else (args.start, "in_progress")
        if not set_status(ref, status):
            print(f"No request found with reference {ref}.")
            return 1
        print(f"{ref.strip().upper()} is now {status}.")
        return 0

    if args.list:
        rows = list_open()
        print(f"{len(rows)} open request(s).\n")
        for row in rows:
            print(format_summary(row), end="\n\n")
        return 0

    server = HTTPServer(("127.0.0.1", DESK_PORT), _Desk)
    print(f"Ops desk (call analytics + mentor queue) on http://127.0.0.1:{DESK_PORT} — Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDesk closed.")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main())
