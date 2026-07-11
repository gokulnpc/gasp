"""SW4 override engagement - shared by the passive watchdog and active tools.

Pages the coordinator (simulated), records the override on the ledger, and
builds the EscalationAgent. The caller decides how to switch:
  - a tool returns the agent (LiveKit handoff)
  - the passive watchdog calls session.update_agent (forced override)
"""

from __future__ import annotations

import logging

import sim
from config import COORDINATOR_PHONE
from data import api as data
from state import CallState

log = logging.getLogger("override")


async def engage(state: CallState, room_name: str, summary: str, source: str):
    """Idempotent per call: returns an EscalationAgent, or None if already engaged."""
    if state.escalation_fired:
        return None
    state.escalation_fired = True
    state.last_intent = "escalation"

    log.warning("SW4 OVERRIDE (%s): %s", source, summary)
    state.push_override("SW4-escalation")
    await data.append_audit_log({"type": "escalation", "summary": summary,
                                 "source": source})
    await sim.send_sms(COORDINATOR_PHONE, f"URGENT escalation: {summary}")
    await sim.dial_into_room(COORDINATOR_PHONE, room_name or "console",
                             "emergency escalation patch-in")

    from subworkflows.sw4_escalation import EscalationAgent
    return EscalationAgent()
