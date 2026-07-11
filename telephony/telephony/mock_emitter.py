"""Day-0 deliverable: scripted call replay so Persons 2 and 4 can build
against the telephony contract with no phone, no Twilio, no LiveKit.

Usage from Person 2/4 code:

    from telephony.event_bus import EventBus
    from telephony.mock_emitter import MockCallEmitter, DEFAULT_CALLOUT_SCRIPT

    bus = EventBus()

    @bus.on_event
    def handle(event):          # <- Person 2's Orchestrator entry point
        print("got", event.type, event.payload)

    emitter = MockCallEmitter(DEFAULT_CALLOUT_SCRIPT, bus)
    emitter.register_command_handlers()   # logs speak/dial/etc. commands
    asyncio.run(emitter.run())

Or standalone from a terminal:  python -m telephony.mock_emitter
"""

from __future__ import annotations

import asyncio
import logging
import time

from .contracts import COMMAND_TYPES, EventEnvelope
from .event_bus import EventBus

logger = logging.getLogger("telephony.mock")

# (delay_since_previous_event_seconds, EventEnvelope)
Script = list[tuple[float, EventEnvelope]]

MOCK_CALL_ID = "call-mock-1"

# Mirrors the demo script in docs/07: a 6 AM call-out with one barge-in.
DEFAULT_CALLOUT_SCRIPT: Script = [
    (0.0, EventEnvelope("participant.joined", MOCK_CALL_ID,
                        {"caller_number": "+15551234567", "room_name": MOCK_CALL_ID})),
    (1.5, EventEnvelope("transcript.final", MOCK_CALL_ID,
                        {"text": "Hi, this is Maria, I can't make my shift today.",
                         "language": "en"})),
    # Caller talks over the agent's reply:
    (4.0, EventEnvelope("barge_in", MOCK_CALL_ID, {})),
    (0.3, EventEnvelope("transcript.final", MOCK_CALL_ID,
                        {"text": "Actually wait, it's for tomorrow's shift, not today.",
                         "language": "en"})),
    # Mid-call intent switch to med-log (exercises Person 2's routing):
    (3.0, EventEnvelope("transcript.final", MOCK_CALL_ID,
                        {"text": "Oh and I still need to log yesterday's medications.",
                         "language": "en"})),
    (5.0, EventEnvelope("call.ended", MOCK_CALL_ID, {"reason": "caller_hangup"})),
]


class MockCallEmitter:
    """Replays a scripted call onto an EventBus with realistic delays and
    logs any commands (speak/stop_speaking/dial/send_sms) sent back."""

    def __init__(self, script: Script, bus: EventBus | None = None) -> None:
        self.script = script
        self.bus = bus or EventBus()
        self.commands_received: list[tuple[str, dict]] = []

    def register_command_handlers(self) -> None:
        """Accept every contract command and just record + log it."""
        for command_type in COMMAND_TYPES:
            @self.bus.on_command(command_type)
            def _handle(command: dict, _type: str = command_type) -> None:
                self.commands_received.append((_type, command))
                logger.info("[mock] command %s: %s", _type, command)

    async def run(self) -> None:
        start = time.monotonic()
        for delay, event in self.script:
            await asyncio.sleep(delay)
            event.ts = time.time()
            logger.info("[mock +%5.1fs] %s %s",
                        time.monotonic() - start, event.type, event.payload)
            self.bus.emit(event)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    emitter = MockCallEmitter(DEFAULT_CALLOUT_SCRIPT)
    emitter.register_command_handlers()

    # Demo subscriber standing in for Person 2's Orchestrator: replies to the
    # first utterance so the command path is exercised too.
    @emitter.bus.on_event
    def auto_responder(event: EventEnvelope) -> None:
        if event.type == "transcript.final" and "shift" in event.payload.get("text", ""):
            emitter.bus.send_command("speak", {
                "call_id": event.call_id,
                "text": "I'm sorry to hear that. Let me confirm which shift you mean.",
                "allow_interruptions": True,
            })

    asyncio.run(emitter.run())
    print(f"\nreplay done — {len(emitter.commands_received)} command(s) received back")


if __name__ == "__main__":
    main()
