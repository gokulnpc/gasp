"""SW2 - Intake & Matching: structured profile -> ranked match -> proposed schedule."""

from __future__ import annotations

from livekit.agents import RunContext, function_tool

from data import api as data
from state import CallState

from .base import GaspWorkflowAgent

INSTRUCTIONS = """\
You run intake for a new patient (usually a family member calling).
1. Collect, conversationally but completely: patient name, zip code,
   languages spoken, and care needs. One or two questions at a time.
2. Once you have them, use match_caregivers and present the TOP match by
   name with WHY (language, certifications, proximity). Offer the runner-up
   only if they decline.
3. Agree a start day/time, then use propose_schedule to book it.
4. Confirm out loud, then use finish_intake.
"""


class IntakeMatchingAgent(GaspWorkflowAgent):
    workflow_name = "SW2-intake-matching"

    def __init__(self, chat_ctx=None) -> None:
        super().__init__(instructions=INSTRUCTIONS, chat_ctx=chat_ctx)

    def entry_prompt(self, state: CallState) -> str:
        return ("Warmly start the new-patient intake: ask for the patient's name "
                "and what kind of help they need.")

    @function_tool
    async def match_caregivers(self, context: RunContext, patient_name: str,
                               zip_code: str, languages: list[str],
                               needs: list[str]):
        """Rank caregivers for the captured patient profile (language, certs, proximity)."""
        state: CallState = context.userdata
        profile = {"name": patient_name, "zip": zip_code,
                   "languages": languages, "needs": needs}
        matches = await data.match_caregivers(profile)
        state.workflow_data["SW2"] = {"profile": profile, "matches": matches}
        state.log("sw2", "match_ranked",
                  ", ".join(f"{m['name']} ({m['match_score']})" for m in matches))
        return {"matches": [{"name": m["name"], "languages": m["languages"],
                             "certifications": m["certifications"],
                             "score": m["match_score"]} for m in matches]}

    @function_tool
    async def propose_schedule(self, context: RunContext, caregiver_name: str,
                               start: str, recurrence: str = "weekly"):
        """Book the agreed caregiver + start time onto the calendar."""
        state: CallState = context.userdata
        sw2 = state.workflow_data.setdefault("SW2", {})
        sw2["schedule"] = {"caregiver": caregiver_name, "start": start,
                           "recurrence": recurrence}
        state.log("sw2", "schedule_proposed", f"{caregiver_name} from {start}")
        await data.append_audit_log({"type": "intake_schedule",
                                     "patient": sw2.get("profile", {}).get("name"),
                                     **sw2["schedule"]})
        return {"booked": True, "caregiver": caregiver_name, "start": start}

    @function_tool
    async def finish_intake(self, context: RunContext):
        """Wrap up intake after confirming; returns to the main assistant."""
        return self.build_orchestrator()
