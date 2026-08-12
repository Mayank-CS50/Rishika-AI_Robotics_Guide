"""Day 6 — place an outbound LFR practice call.

Usage:
    uv run python src/dispatch_outbound.py --to +919876543210
    uv run python src/dispatch_outbound.py --to +919876543210 --name Ramesh

Requires the agent worker to already be running (`uv run python src/agent.py start`).
The worker dials out itself; this script only creates the room + dispatch.
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys

from dotenv import load_dotenv
from livekit import api

import db_memory

load_dotenv(".env.local")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("dispatch-outbound")

AGENT_NAME = os.getenv("AGENT_NAME", "Rishika")


async def dispatch(phone: str, name: str) -> int:
    if not os.getenv("SIP_OUTBOUND_TRUNK_ID"):
        logger.error("SIP_OUTBOUND_TRUNK_ID missing from .env.local — run setup_sip_trunk.py first.")
        return 2

    if db_memory.is_opted_out(phone):
        logger.error(f"{phone} has opted out of practice calls. Not dialing.")
        return 3

    # Reuse the saved profile so the call opens with their actual last topic.
    record = db_memory.get_user(name) if name else None
    metadata = {
        "phone_number": phone,
        "student_name": (record or {}).get("name") or name,
        "last_topic": (record or {}).get("topics_covered", ""),
        "level": (record or {}).get("current_level", ""),
    }

    room_name = "lfr-practice-" + re.sub(r"[^a-zA-Z0-9_-]", "-", phone.lstrip("+"))

    async with api.LiveKitAPI() as lk:
        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )

    logger.info(f"Dispatched {AGENT_NAME} to call {phone} in room {room_name}")
    if record:
        logger.info(f"Returning student: {record['name']} — last topic: {record['topics_covered']}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Place an outbound LFR practice call.")
    p.add_argument(
        "--to",
        required=True,
        help="E.164 number (+919876543210) or a SIP username for a softphone trunk",
    )
    p.add_argument("--name", default="", help="Student name, to load their saved progress")
    p.add_argument(
        "--allow-again",
        action="store_true",
        help="Clear this target's opt-out first (you demoed 'stop calling' and want to re-dial)",
    )
    args = p.parse_args()

    # A SIP-user target (softphone) is valid too, so only sanity-check actual phone numbers.
    if args.to[:1].isdigit():
        logger.error("Phone numbers must be E.164 and start with '+' (e.g. +919876543210).")
        return 1

    if args.allow_again and db_memory.remove_opt_out(args.to):
        logger.info(f"Cleared the earlier opt-out for {args.to}.")

    return asyncio.run(dispatch(args.to, args.name))


if __name__ == "__main__":
    sys.exit(main())
