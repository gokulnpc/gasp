"""Fix SIP dispatch rule: attach gasp-agent so inbound calls reach THIS worker.

The existing gasp-dispatch rule creates call-* rooms but had agents=[] —
calls rang with nobody answering. Run once:

  cd gasp/agent && .venv/bin/python fix_sip_dispatch.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv
from livekit import api

load_dotenv()

RULE_NAME = "gasp-dispatch"
AGENT = os.getenv("GASP_AGENT_NAME", "gasp-agent")
INBOUND_TRUNK_NAME = "gasp-inbound"


async def main() -> None:
    for var in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"):
        if not os.getenv(var):
            sys.exit(f"missing {var}")

    lk = api.LiveKitAPI()
    try:
        inb = await lk.sip.list_sip_inbound_trunk(api.ListSIPInboundTrunkRequest())
        trunk = next((t for t in inb.items if t.name == INBOUND_TRUNK_NAME), None)
        if trunk is None:
            sys.exit(f"inbound trunk {INBOUND_TRUNK_NAME!r} not found — run gasp/telephony/scripts/setup_livekit_sip.py")

        rules = await lk.sip.list_sip_dispatch_rule(api.ListSIPDispatchRuleRequest())
        old = next((r for r in rules.items if r.name == RULE_NAME), None)
        if old:
            await lk.sip.delete_sip_dispatch_rule(
                api.DeleteSIPDispatchRuleRequest(sip_dispatch_rule_id=old.sip_dispatch_rule_id)
            )
            print(f"deleted old rule {old.sip_dispatch_rule_id}")

        rule = await lk.sip.create_sip_dispatch_rule(
            api.CreateSIPDispatchRuleRequest(
                name=RULE_NAME,
                trunk_ids=[trunk.sip_trunk_id],
                rule=api.SIPDispatchRule(
                    dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                        room_prefix="call-",
                    )
                ),
                room_config=api.RoomConfiguration(
                    agents=[api.RoomAgentDispatch(agent_name=AGENT)],
                ),
            )
        )
        print(f"created dispatch rule {rule.sip_dispatch_rule_id}")
        print(f"  rooms: call-*")
        print(f"  agent: {AGENT}")
        print(f"\nInbound: dial {os.getenv('TWILIO_VOICE_NUMBER', '+19297307867')}")
        print(f"Then run:  .venv/bin/python main.py dev")
    finally:
        await lk.aclose()


if __name__ == "__main__":
    asyncio.run(main())
