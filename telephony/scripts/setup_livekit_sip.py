"""One-time LiveKit SIP setup: inbound trunk + dispatch rule + outbound trunk.

Run once against Person 2's LiveKit project (needs LIVEKIT_URL / API key /
secret in .env). Idempotent-ish: lists existing resources first and skips
creation if a trunk/rule with our name already exists.

The Twilio side (trunk Arya-Hack / TK21e8a9e33f9963c6ce2255b049e8cce0) is
already configured in the Console:
  - Origination URI -> sip:5bwxm1tai7w.sip.livekit.cloud  (inbound path)
  - Termination URI + credential list                     (outbound path)
  - Number +19297307867 attached

Usage:  python scripts/setup_livekit_sip.py
Then copy the printed outbound trunk ID into .env as LIVEKIT_SIP_OUTBOUND_TRUNK_ID.
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv
from livekit import api

load_dotenv()

INBOUND_TRUNK_NAME = "gasp-inbound"
OUTBOUND_TRUNK_NAME = "gasp-outbound"
DISPATCH_RULE_NAME = "gasp-dispatch"
ROOM_PREFIX = "call-"  # room-naming convention shared with Person 2

VOICE_NUMBER = os.getenv("TWILIO_VOICE_NUMBER", "+19297307867")
TERMINATION_URI = os.getenv("TWILIO_TERMINATION_URI", "")  # e.g. arya-hack.pstn.twilio.com
SIP_USERNAME = os.getenv("TWILIO_SIP_USERNAME", "")
SIP_PASSWORD = os.getenv("TWILIO_SIP_PASSWORD", "")


async def main() -> None:
    for var in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"):
        if not os.getenv(var):
            sys.exit(f"missing {var} in .env — get LiveKit credentials from Person 2")

    lk = api.LiveKitAPI()  # reads LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET

    try:
        # -- 1. inbound trunk: accepts calls Twilio originates to LiveKit ----
        existing_in = await lk.sip.list_sip_inbound_trunk(api.ListSIPInboundTrunkRequest())
        inbound = next((t for t in existing_in.items if t.name == INBOUND_TRUNK_NAME), None)
        if inbound is None:
            inbound = await lk.sip.create_sip_inbound_trunk(
                api.CreateSIPInboundTrunkRequest(
                    trunk=api.SIPInboundTrunkInfo(
                        name=INBOUND_TRUNK_NAME,
                        numbers=[VOICE_NUMBER],
                        krisp_enabled=True,
                    )
                )
            )
            print(f"created inbound trunk: {inbound.sip_trunk_id}")
        else:
            print(f"inbound trunk exists: {inbound.sip_trunk_id}")

        # -- 2. dispatch rule: one room per call, named call-<xxxx> ----------
        existing_rules = await lk.sip.list_sip_dispatch_rule(api.ListSIPDispatchRuleRequest())
        rule = next((r for r in existing_rules.items if r.name == DISPATCH_RULE_NAME), None)
        if rule is None:
            rule = await lk.sip.create_sip_dispatch_rule(
                api.CreateSIPDispatchRuleRequest(
                    name=DISPATCH_RULE_NAME,
                    trunk_ids=[inbound.sip_trunk_id],
                    rule=api.SIPDispatchRule(
                        dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                            room_prefix=ROOM_PREFIX,
                        )
                    ),
                )
            )
            print(f"created dispatch rule: {rule.sip_dispatch_rule_id} (rooms: {ROOM_PREFIX}*)")
        else:
            print(f"dispatch rule exists: {rule.sip_dispatch_rule_id}")

        # -- 3. outbound trunk: cascade calls out through Twilio Termination -
        if not (TERMINATION_URI and SIP_USERNAME and SIP_PASSWORD):
            print("skipping outbound trunk: set TWILIO_TERMINATION_URI / "
                  "TWILIO_SIP_USERNAME / TWILIO_SIP_PASSWORD in .env first")
            return

        existing_out = await lk.sip.list_sip_outbound_trunk(api.ListSIPOutboundTrunkRequest())
        outbound = next((t for t in existing_out.items if t.name == OUTBOUND_TRUNK_NAME), None)
        if outbound is None:
            outbound = await lk.sip.create_sip_outbound_trunk(
                api.CreateSIPOutboundTrunkRequest(
                    trunk=api.SIPOutboundTrunkInfo(
                        name=OUTBOUND_TRUNK_NAME,
                        address=TERMINATION_URI,
                        numbers=[VOICE_NUMBER],
                        auth_username=SIP_USERNAME,
                        auth_password=SIP_PASSWORD,
                    )
                )
            )
            print(f"created outbound trunk: {outbound.sip_trunk_id}")
        else:
            print(f"outbound trunk exists: {outbound.sip_trunk_id}")

        print(f"\n-> put this in .env:  LIVEKIT_SIP_OUTBOUND_TRUNK_ID={outbound.sip_trunk_id}")
    finally:
        await lk.aclose()


if __name__ == "__main__":
    asyncio.run(main())
