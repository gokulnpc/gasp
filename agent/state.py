"""Shared call state: the Passive Agent's context ledger.

One CallState object per call, carried as AgentSession.userdata so every
tool, SubWorkflow agent, and the passive listener mutate the SAME state.
The ledger (events) is append-only; snapshots are cheap dict copies the
Active Agent can pull after a barge-in or intent switch.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from pydantic import BaseModel, Field


class LedgerEvent(BaseModel):
    ts: float = Field(default_factory=time.time)
    source: str          # orchestrator | passive | sw1..sw4 | cascade | sim
    kind: str            # caller_identified | intent_detected | workflow_entered | ...
    detail: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class Turn(BaseModel):
    ts: float = Field(default_factory=time.time)
    role: str            # user | assistant
    text: str


class CallState(BaseModel):
    call_id: str
    caller_phone: str = ""
    room_name: str = ""
    started_at: float = Field(default_factory=time.time)
    ended_at: Optional[float] = None

    caller: Optional[dict[str, Any]] = None      # caregiver/patient profile once identified
    language: str = "english"

    active_workflow: Optional[str] = None
    workflow_stack: list[str] = Field(default_factory=list)   # for SW4 override/restore
    workflow_data: dict[str, Any] = Field(default_factory=dict)  # per-SW scratch space

    transcript: list[Turn] = Field(default_factory=list)
    events: list[LedgerEvent] = Field(default_factory=list)
    last_intent: str = "unknown"

    escalation_fired: bool = False
    summary_emitted: bool = False
    summary: Optional[dict[str, Any]] = None

    # ---- ledger API (Passive Agent owns the semantics, everyone may append) ----

    def log(self, source: str, kind: str, detail: str = "", **data: Any) -> None:
        self.events.append(LedgerEvent(source=source, kind=kind, detail=detail, data=data))

    def snapshot(self) -> dict[str, Any]:
        """Latest state snapshot - what the Active Agent pulls after a barge-in."""
        return {
            "caller": (self.caller or {}).get("name"),
            "language": self.language,
            "active_workflow": self.active_workflow,
            "workflow_stack": list(self.workflow_stack),
            "last_intent": self.last_intent,
            "workflow_data": self.workflow_data,
            "recent_events": [
                {"kind": e.kind, "detail": e.detail} for e in self.events[-8:]
            ],
        }

    def enter_workflow(self, name: str, source: str = "orchestrator") -> None:
        if self.active_workflow and self.active_workflow != name:
            self.log(source, "workflow_exited", self.active_workflow)
        self.active_workflow = name
        self.log(source, "workflow_entered", name)

    def push_override(self, override: str) -> None:
        """SW4 interrupts: remember what was active so we can restore it."""
        if self.active_workflow and self.active_workflow != override:
            self.workflow_stack.append(self.active_workflow)
        self.active_workflow = override
        self.log("passive", "override_engaged", override)

    def pop_override(self) -> Optional[str]:
        prior = self.workflow_stack.pop() if self.workflow_stack else None
        self.active_workflow = prior
        self.log("passive", "override_released", prior or "none")
        return prior
