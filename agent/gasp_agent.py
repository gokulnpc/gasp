"""Shared GASP agent base: PII guardrail on the LLM ingestion path."""

from __future__ import annotations

from livekit.agents import Agent, llm

from config import PII_REDACTION_ENABLED
from pii import scrub_for_llm


class GaspAgent(Agent):
    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        if not PII_REDACTION_ENABLED:
            return

        hits = scrub_for_llm(turn_ctx, new_message)
        if not hits:
            return

        state = getattr(self.session, "userdata", None)
        if state is not None:
            state.log("guardrail", "pii_redacted", ", ".join(hits))
