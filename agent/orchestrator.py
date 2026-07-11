"""Main Orchestrator Agent - the hub: recognize the caller, detect intent, route.

Routing happens two ways, by design:
  - actively: this agent's route_* tools hand off to a SubWorkflow agent
  - passively: passive.py watches every turn and force-routes SW4 on distress

Chat context travels across handoffs, so a mid-call intent switch closes one
workflow and opens another without dropping the call or losing state (FR-2).
"""

from __future__ import annotations

from typing import Optional

from livekit.agents import Agent, RunContext, function_tool, llm

import override
from data import api as data
from state import CallState
from subworkflows.base import VOICE_RULES

INSTRUCTIONS = """\
You are Ava, the phone assistant for Sunrise Home Care, a home-health agency.
You are the front door for every call: recognize the caller, find out what they
need, and route them.

1. Use identify_caller FIRST - you already have their number - then greet by name.
   If unknown, ask who they are.
2. Detect what they need and route with exactly one tool:
   - can't make / cancelling a shift        -> route_shift_callout
   - closing out a shift / logging meds     -> route_medlog
   - new patient or family seeking care     -> route_intake
   - ACTIVE emergency or demands a human    -> route_escalation (do this FIRST,
     before anything else, if there is any sign of danger)
3. If they were mid-task before (see get_state_snapshot), offer to pick up where
   they left off.
4. Stay on healthcare-agency topics. Never invent shifts, patients, or meds.
"""


class OrchestratorAgent(Agent):
    workflow_name = "orchestrator"

    def __init__(self, chat_ctx: Optional[llm.ChatContext] = None) -> None:
        super().__init__(instructions=VOICE_RULES + INSTRUCTIONS, chat_ctx=chat_ctx)

    @property
    def call_state(self) -> CallState:
        return self.session.userdata

    async def on_enter(self) -> None:
        state = self.call_state
        if not state.transcript:
            state.log("orchestrator", "call_answered", state.caller_phone)
            prompt = ("Greet the caller: this is Ava at Sunrise Home Care. "
                      "Use identify_caller, greet them by name, ask how you can help.")
        else:
            prompt = ("The previous task is wrapped up. Briefly ask if there is "
                      "anything else you can help with.")
        self.session.generate_reply(instructions=prompt)

    # ---- identity & state ----

    @function_tool
    async def identify_caller(self, context: RunContext):
        """Look up who is calling from their phone number. Use before asking names."""
        state: CallState = context.userdata
        caller = await data.get_caller_by_phone(state.caller_phone)
        if not caller:
            state.log("orchestrator", "caller_unknown", state.caller_phone)
            return {"found": False, "phone": state.caller_phone}
        state.caller = caller
        state.log("orchestrator", "caller_identified", caller["name"])
        return {"found": True, "name": caller["name"],
                "languages": caller["languages"]}

    @function_tool
    async def get_state_snapshot(self, context: RunContext):
        """Pull the latest call-state snapshot (active workflow, recent events)."""
        state: CallState = context.userdata
        return state.snapshot()

    # ---- routing (intent -> SubWorkflow) ----

    @function_tool
    async def route_shift_callout(self, context: RunContext):
        """Route to the shift-backfill workflow: caller cannot make a shift."""
        return self._route(context, "shift_callout", "SW1-shift-backfill")

    @function_tool
    async def route_medlog(self, context: RunContext):
        """Route to the med-log workflow: caregiver closing out a shift."""
        return self._route(context, "medlog", "SW3-medlog")

    @function_tool
    async def route_intake(self, context: RunContext):
        """Route to new-patient intake and caregiver matching."""
        return self._route(context, "intake", "SW2-intake-matching")

    @function_tool
    async def route_escalation(self, context: RunContext, summary: str):
        """Emergency override: pages the human coordinator and patches them in.
        Use IMMEDIATELY on any active medical/safety emergency or 'get me a human'."""
        state: CallState = context.userdata
        state.last_intent = "escalation"
        agent = await override.engage(state, state.room_name, summary, source="active")
        if agent is None:
            return {"already_escalated": True}
        return agent

    def _route(self, context: RunContext, intent: str, workflow: str):
        state: CallState = context.userdata
        state.last_intent = intent
        state.log("orchestrator", "intent_routed", f"{intent} -> {workflow}")
        import subworkflows
        return subworkflows.build(workflow, chat_ctx=self.chat_ctx)
