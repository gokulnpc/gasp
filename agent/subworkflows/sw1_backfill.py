"""SW1 - Shift-Backfill Cascade: call-out -> vacancy -> cascade -> first YES locks."""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from data import api as data
from state import CallState

from .base import GaspWorkflowAgent

INSTRUCTIONS = """\
You handle a caregiver calling out of a shift.
1. If the caller is not identified yet, ask their name once and use
   identify_by_name (a first name is enough).
2. Use list_shifts and confirm out loud WHICH shift they mean (client + time).
   Never guess and never ask for IDs - the tools handle matching.
3. Ask briefly why they can't make it (one short question) - if they already
   told you, don't ask again.
4. Use record_callout with the shift_id from list_shifts (or the client name
   if you don't have the id). That queues the backfill job - reassure them
   replacement outreach has already started.
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
            return {"error": "caller not identified yet - ask their name, "
                             "then use identify_by_name"}
        shifts = await data.upcoming_shifts(state.caller["id"])
        state.log("sw1", "shifts_listed", f"{len(shifts)} upcoming")
        if not shifts:
            return {"shifts": [], "note": "no open shifts found for this caregiver"}
        return {"shifts": shifts}

    @function_tool
    async def record_callout(self, context: RunContext, shift_id: str, reason: str):
        """Record the callout and queue the backfill job. shift_id can be the id
        from list_shifts OR a spoken reference like 'the Patterson shift'."""
        try:
            state: CallState = context.userdata
            cid = (state.caller or {}).get("id")
            shift = await data.resolve_shift(shift_id, cid)
            if not shift:
                return {"error": f"could not match {shift_id!r} to a shift - "
                                 "use list_shifts and confirm with the caller"}
            job = await data.create_callout(shift["id"], cid, reason)
            state.workflow_data["SW1"] = {"shift_id": shift["id"], "reason": reason,
                                          "callout_id": job.get("id")}
            state.log("sw1", "callout_queued", f"{shift['client_name']}: {reason}")
            return {"recorded": True, "callout_id": job.get("id"),
                    "shift": {"client": shift["client_name"],
                              "starts_at": shift["starts_at"]},
                    "coverage": "replacement outreach queued - worker is on it"}
        except Exception as exc:
            return {"error": str(exc)}

    @function_tool
    async def finish_backfill(self, context: RunContext):
        """Hand control back to the main assistant when the callout is fully handled."""
        return self.build_orchestrator()
