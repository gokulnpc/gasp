"""SW3 - Med-Log & Compliance: strict per-med questionnaire -> structured JSON -> audit log."""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from data import api as data
from state import CallState

from .base import GaspWorkflowAgent

INSTRUCTIONS = """\
You run the end-of-shift medication check-in. This is a compliance questionnaire:
be warm but strict, one medication at a time.
1. Use get_med_layout for the patient on the shift being closed out.
2. For EACH scheduled med ask: was it given, at what time, any issues?
   Allowed statuses: given, missed, refused, prn_given, prn_not_needed.
3. Record each answer with log_medication immediately after the caregiver confirms it.
4. NEVER invent meds, doses, or times. If the caregiver corrects an earlier answer,
   call log_medication again - corrections are new entries, nothing is overwritten.
5. After all meds: read back a short summary, then use finish_medlog.
"""


class MedLogAgent(GaspWorkflowAgent):
    workflow_name = "SW3-medlog"

    def __init__(self, chat_ctx=None) -> None:
        super().__init__(instructions=INSTRUCTIONS, chat_ctx=chat_ctx)

    def entry_prompt(self, state: CallState) -> str:
        return ("Tell the caller you'll run the quick end-of-shift medication check "
                "and use get_med_layout to load the list, then ask about the first med.")

    @function_tool
    async def get_med_layout(self, context: RunContext, shift_id: str = ""):
        """Load the patient's daily medication layout for the shift being closed out."""
        state: CallState = context.userdata
        if not shift_id:
            shifts = await data.upcoming_shifts((state.caller or {}).get("id", ""))
            shift_id = shifts[0]["id"] if shifts else ""
        shift = await data.get_shift(shift_id)
        if not shift:
            return {"error": "no shift found - ask which visit they are closing out"}
        # Supabase shifts carry no patient_id (med layouts are still mocked)
        patient_id = shift.get("patient_id", "")
        layout = await data.get_med_layout(patient_id)
        state.workflow_data["SW3"] = {"shift_id": shift_id,
                                      "patient_id": patient_id,
                                      "entries": []}
        state.log("sw3", "med_layout_loaded",
                  f"{shift['client_name']}: {len(layout)} meds")
        return {"patient": shift["client_name"], "medications": layout}

    @function_tool
    async def log_medication(self, context: RunContext, med_id: str, med_name: str,
                             status: str, time_given: str = "", notes: str = ""):
        """Record one confirmed medication answer.
        status: given | missed | refused | prn_given | prn_not_needed."""
        state: CallState = context.userdata
        sw3 = state.workflow_data.setdefault("SW3", {"entries": []})
        entry = {"med_id": med_id, "med_name": med_name, "status": status,
                 "time_given": time_given, "notes": notes,
                 "shift_id": sw3.get("shift_id"), "patient_id": sw3.get("patient_id"),
                 "caregiver_id": (state.caller or {}).get("id")}
        sw3["entries"].append(entry)
        state.log("sw3", "med_logged", f"{med_name}: {status}")
        await data.append_audit_log({"type": "med_log", **entry})
        return {"logged": True, "so_far": len(sw3["entries"])}

    @function_tool
    async def finish_medlog(self, context: RunContext):
        """Close the med-log after reading back the summary; returns to the main assistant."""
        state: CallState = context.userdata
        entries = state.workflow_data.get("SW3", {}).get("entries", [])
        await data.append_audit_log({"type": "med_log_complete",
                                     "count": len(entries),
                                     "shift_id": state.workflow_data.get("SW3", {}).get("shift_id")})
        return self.build_orchestrator()
