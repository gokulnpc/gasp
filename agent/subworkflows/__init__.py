"""SubWorkflow registry: name -> builder, used for SW4 override restore."""

from __future__ import annotations

from typing import Optional

from livekit.agents import llm


def build(workflow_name: str, chat_ctx: Optional[llm.ChatContext] = None):
    """Rebuild a workflow agent by ledger name (late imports avoid cycles)."""
    from .sw1_backfill import ShiftBackfillAgent
    from .sw2_intake import IntakeMatchingAgent
    from .sw3_medlog import MedLogAgent
    from .sw4_escalation import EscalationAgent

    registry = {
        "SW1-shift-backfill": ShiftBackfillAgent,
        "SW2-intake-matching": IntakeMatchingAgent,
        "SW3-medlog": MedLogAgent,
        "SW4-escalation": EscalationAgent,
    }
    cls = registry[workflow_name]
    return cls(chat_ctx=chat_ctx)
