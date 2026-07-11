"""SubWorkflow contract over LiveKit agents (docs/09 seam, Person 2 owns this).

Mapping of the agreed enter/handleTurn/exit contract onto LiveKit:
  enter(ctx)              -> Agent.on_enter (ledger event + opening reply)
  handleTurn(utterance)   -> the LLM turn loop + this agent's @function_tool methods
  exit()                  -> finish_* tool / on_exit (ledger event + handoff back)

Shared state object = CallState carried in AgentSession.userdata; every
workflow reads/writes the same ledger, so intent switches and barge-ins
never lose context (the chat_ctx is also handed across agents).
"""

from __future__ import annotations

from typing import Optional

from livekit.agents import Agent, llm

from state import CallState

VOICE_RULES = (
    "This is a live phone call: reply in one or two short conversational "
    "sentences, no lists or markdown, say times naturally ('ten A M'). "
    "If the caller switches topic mid-flow, acknowledge it, use your finish "
    "tool to hand control back, and never drop the call. "
)


class GaspWorkflowAgent(Agent):
    """Base for SW1-SW4: logs enter/exit to the ledger automatically."""

    workflow_name: str = "SW?"

    def __init__(self, instructions: str,
                 chat_ctx: Optional[llm.ChatContext] = None) -> None:
        super().__init__(instructions=VOICE_RULES + instructions, chat_ctx=chat_ctx)

    @property
    def call_state(self) -> CallState:
        return self.session.userdata

    async def on_enter(self) -> None:
        state = self.call_state
        if state.active_workflow != self.workflow_name:
            state.enter_workflow(self.workflow_name)
        self.session.generate_reply(instructions=self.entry_prompt(state))

    def entry_prompt(self, state: CallState) -> str:
        """What to say when this workflow takes over. Override per workflow."""
        return "Briefly confirm what the caller needs and continue."

    def build_orchestrator(self):
        """Handoff target for finish tools (late import avoids cycles)."""
        from orchestrator import OrchestratorAgent
        state = self.call_state
        state.log(self.workflow_name.split("-")[0].lower(), "workflow_completed",
                  self.workflow_name)
        state.active_workflow = None
        return OrchestratorAgent(chat_ctx=self.chat_ctx)
