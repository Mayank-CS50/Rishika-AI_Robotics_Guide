"""One-time: register an outbound SIP trunk with LiveKit.

    uv run python src/setup_sip_trunk.py

Works for either destination:
  * a PSTN carrier  — SIP_TRUNK_ADDRESS=your-trunk.pstn.twilio.com  (costs money)
  * a SIP registrar — SIP_TRUNK_ADDRESS=sip.linphone.org            (free, softphone rings)

LiveKit sends the INVITE to sip:<--to>@<SIP_TRUNK_ADDRESS>, so the address decides
whether you reach a phone network or a softphone account.

Prints the trunk id — paste it into .env.local as SIP_OUTBOUND_TRUNK_ID.
Re-running lists existing trunks instead of creating duplicates.
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("setup-sip-trunk")

REQUIRED = ["TWILIO_SIP_TERM_URI", "TWILIO_SIP_USERNAME", "TWILIO_SIP_PASSWORD", "TWILIO_PHONE_NUMBER"]


def _address() -> str:
    """Destination host. SIP_TRUNK_ADDRESS wins; TWILIO_SIP_TERM_URI kept for the PSTN path."""
    return os.getenv("SIP_TRUNK_ADDRESS") or os.getenv("TWILIO_SIP_TERM_URI") or ""


async def setup() -> int:
    address = _address()
    if not address:
        logger.error("Set SIP_TRUNK_ADDRESS (e.g. sip.linphone.org) in .env.local.")
        return 1

    # A free registrar needs no caller-ID number and often no auth; a carrier needs both.
    number = os.getenv("TWILIO_PHONE_NUMBER") or "*"
    username = os.getenv("SIP_TRUNK_USERNAME") or os.getenv("TWILIO_SIP_USERNAME") or ""
    password = os.getenv("SIP_TRUNK_PASSWORD") or os.getenv("TWILIO_SIP_PASSWORD") or ""

    async with api.LiveKitAPI() as lk:
        existing = await lk.sip.list_sip_outbound_trunk(api.ListSIPOutboundTrunkRequest())
        for trunk in existing.items:
            if trunk.address == address:
                logger.info(f"Trunk already exists — SIP_OUTBOUND_TRUNK_ID={trunk.sip_trunk_id}")
                return 0

        trunk = await lk.sip.create_sip_outbound_trunk(
            api.CreateSIPOutboundTrunkRequest(
                trunk=api.SIPOutboundTrunkInfo(
                    name=f"Rishika LFR Outbound ({address})",
                    address=address,
                    numbers=[number],
                    auth_username=username,
                    auth_password=password,
                )
            )
        )

    logger.info(f"Created trunk for {address}. Add this to .env.local:\n\nSIP_OUTBOUND_TRUNK_ID={trunk.sip_trunk_id}\n")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(setup()))
