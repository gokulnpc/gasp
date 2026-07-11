"""SW1 - Shift-Backfill Cascade: call-out -> vacancy -> cascade -> first YES locks."""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from data import api as data
from state import CallState

from .base import GaspWorkflowAgent

INSTRUCTIONS = """\
You handle a caregiver calling out of a shift.
1. If the caller is not identified yet, ask who they are; otherwise use their name.
2. Use list_shifts and confirm out loud WHICH shift they mean (client + time). Never guess.
3. Ask briefly why they can't make it (one short question).
4. Use record_callout. That queues a backfill job in Supabase - reassure them
   outreach has already started. A separate worker picks it up immediately.
5. When done (or caller changes topic), use finish_backfill.
"""


class ShiftBackfillAgent(GaspWorkflowAgent):
    workflow_name = "SW1-shift-backfill"

    def __init__(self, chat_ctx=None) -> None:
        super().__init__(instructions=INSTRUCTIONS, chat_ctx=chat_ctx)

    def entry_prompt(self, state: CallState) -> str:
        name = (state.caller or {}).get("name", "")
        return (f"Express brief sympathy to {name or 'the caller'} about missing their "
                "shift, then confirm which shift they mean using list_shifts.")

    @function_tool
    async def list_shifts(self, context: RunContext):
        """List the caller's upcoming shifts so you can confirm which one they mean."""
        state: CallState = context.userdata
        if not state.caller:
            return {"error": "caller not identified yet - ask who they are"}
        shifts = await data.upcoming_shifts(state.caller["id"])
        state.log("sw1", "shifts_listed", f"{len(shifts)} upcoming")
        return {"shifts": shifts}

    @function_tool
    async def record_callout(self, context: RunContext, shift_id: str, reason: str):
        """Record the callout and queue a Supabase job for the dispatch worker."""
        try:
            state: CallState = context.userdata
            shift = await data.get_shift(shift_id)
            if not shift:
                return {"error": f"unknown shift {shift_id}"}
            cid = (state.caller or {}).get("id")
            job = await data.create_callout(shift_id, cid, reason)
            state.workflow_data["SW1"] = {"shift_id": shift_id, "reason": reason,
                                          "callout_id": job.get("id")}
            state.log("sw1", "callout_queued", f"{shift_id}: {reason}")
            return {"recorded": True, "callout_id": job.get("id"),
                    "coverage": "replacement outreach queued - worker is on it"}
        except Exception as exc:
            return {"error": str(exc)}

    @function_tool
    async def finish_backfill(self, context: RunContext):
        """Hand control back to the main assistant when the callout is fully handled."""
        return self.build_orchestrator()
