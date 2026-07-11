"""SW4 - Interpreter & Escalation Bridge (always-on override).

Entered two ways:
  - passively: the keyword watchdog spots distress and force-switches the session
  - actively: any workflow's LLM hears an emergency and routes here

Coordinator paging + patch-in are simulated (sim.py). On resolution the
prior workflow is restored from the ledger stack - context intact.
"""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

import sim
import subworkflows
from config import COORDINATOR_PHONE
from data import api as data
from state import CallState

from .base import GaspWorkflowAgent

INSTRUCTIONS = """\
You are now in emergency escalation mode. A human coordinator has been paged
and is being patched into this call.
1. Stay calm, keep the caller safe: short reassuring sentences. If life-threatening,
   tell them to call 911 first. No medical advice beyond that.
2. If the caller speaks another language, act as a live two-way interpreter between
   them and the English-speaking coordinator: relay each side faithfully, first person.
3. Stay in this mode while the emergency is active.
4. Only when the caller confirms things are handled (or it was a false alarm), use
   resolve_escalation to return to what they were doing before.
"""


class EscalationAgent(GaspWorkflowAgent):
    workflow_name = "SW4-escalation"

    def __init__(self, chat_ctx=None) -> None:
        super().__init__(instructions=INSTRUCTIONS, chat_ctx=chat_ctx)

    def entry_prompt(self, state: CallState) -> str:
        lang = state.language
        prefix = (f"Respond in {lang}. " if lang != "english" else "")
        return (prefix + "Calmly tell the caller the coordinator has been paged and is "
                "being connected right now, and ask if they are somewhere safe.")

    @function_tool
    async def resolve_escalation(self, context: RunContext, outcome: str):
        """Close the escalation once the caller confirms it's handled.
        outcome: e.g. 'coordinator took over', 'false alarm', 'caller safe'."""
        state: CallState = context.userdata
        state.log("sw4", "escalation_resolved", outcome)
        await data.append_audit_log({"type": "escalation_resolved", "outcome": outcome})
        await sim.send_sms(COORDINATOR_PHONE, f"Escalation resolved: {outcome}")

        prior = state.pop_override()
        if prior and prior != self.workflow_name:
            state.enter_workflow(prior, source="sw4")
            return subworkflows.build(prior, chat_ctx=self.chat_ctx)
        return self.build_orchestrator()
