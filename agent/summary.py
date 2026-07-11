"""Post-call structured summary (FR-9): the receipt pushed to the staff portal.

Deterministic build from the ledger (never blocks on an LLM), printed as a
banner and appended to portal_summaries.jsonl - the mock staff portal.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from config import PORTAL_LOG
from data import api as data
from state import CallState

log = logging.getLogger("summary")


def build(state: CallState) -> dict[str, Any]:
    workflows = [e.detail for e in state.events if e.kind == "workflow_entered"]
    sw1 = state.workflow_data.get("SW1", {})
    sw2 = state.workflow_data.get("SW2", {})
    sw3 = state.workflow_data.get("SW3", {})
    return {
        "call_id": state.call_id,
        "caller": (state.caller or {}).get("name") or state.caller_phone,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(state.started_at)),
        "duration_s": round((state.ended_at or time.time()) - state.started_at),
        "workflows": workflows,
        "final_intent": state.last_intent,
        "callout": ({"shift_id": sw1.get("shift_id"), "reason": sw1.get("reason"),
                     "filled_by": sw1.get("filled_by", "cascade in progress")}
                    if sw1 else None),
        "intake": ({"patient": sw2.get("profile", {}).get("name"),
                    "schedule": sw2.get("schedule")} if sw2 else None),
        "med_log": ({"entries": sw3.get("entries", [])} if sw3 else None),
        "escalation": state.escalation_fired,
        "turns": len(state.transcript),
        "ledger_events": len(state.events),
    }


async def emit(state: CallState, reason: str) -> None:
    """Exactly-once emission to console + portal file + audit log."""
    if state.summary_emitted:
        return
    state.summary_emitted = True
    state.ended_at = state.ended_at or time.time()

    state.summary = build(state)
    await data.append_audit_log({"type": "call_summary", **state.summary})
    with PORTAL_LOG.open("a") as f:
        f.write(json.dumps(state.summary) + "\n")

    pretty = json.dumps(state.summary, indent=2)
    log.info("POST-CALL SUMMARY (%s)\n%s\n%s\n%s", reason, "=" * 56, pretty, "=" * 56)
