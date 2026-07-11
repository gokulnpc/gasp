"""Passive Agent - the lean context ledger + escalation safety net.

Runs OFF the voice path. On every finalized turn it appends to the ledger,
and - using cheap keyword matching (no LLM, no network) - force-switches to
SW4 if the caller signals distress and the Active Agent hasn't already.

Routing for everything else is the Active Orchestrator's job (its LLM picks
a route_* tool), so we deliberately DON'T duplicate intent detection here -
that keeps every turn fast and the code simple.
"""

from __future__ import annotations

import asyncio
import logging

from livekit.agents import AgentSession

import override
import summary as summary_mod
from state import CallState, Turn

log = logging.getLogger("passive")

# Active emergency / "get me a human" signals the Active Agent must never miss.
ESCALATION_WORDS = (
    "bleeding", "chest pain", "can't breathe", "cannot breathe", "unconscious",
    "911", "hospital", "severe pain", "heart attack", "stroke", "passed out",
    "get me a human", "real person", "speak to a human", "talk to a person",
    "help me now",
)


def _is_escalation(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in ESCALATION_WORDS)


def wire_passive(session: AgentSession, state: CallState) -> None:
    @session.on("conversation_item_added")
    def _on_item(event) -> None:
        item = getattr(event, "item", None)
        role = getattr(item, "role", None)
        text = (getattr(item, "text_content", "") or "").strip()
        if role not in ("user", "assistant") or not text:
            return
        state.transcript.append(Turn(role=role, text=text))
        if role == "user" and _is_escalation(text) and not state.escalation_fired:
            asyncio.create_task(_escalate(session, state, text))

    @session.on("close")
    def _on_close(event) -> None:
        asyncio.create_task(summary_mod.emit(state, reason="session closed"))


async def _escalate(session: AgentSession, state: CallState, text: str) -> None:
    """Force the SW4 override mid-flow; never lets a failure hurt the call."""
    try:
        agent = await override.engage(state, state.room_name,
                                      f"caller said: {text}", source="passive")
        if agent is not None:
            session.update_agent(agent)
    except Exception:
        log.exception("passive escalation failed (voice loop unaffected)")
