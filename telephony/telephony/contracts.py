"""The Hour-0 event/command contract between Person 1 (telephony) and Persons 2/4.

Events flow Person 1 -> Person 2 (Orchestrator/Passive Agent).
Commands flow Person 2/4 -> Person 1 (voice agent / outbound transport).

Transport is in-process (per team decision) — these shapes are plain
dataclasses/TypedDicts passed through `event_bus.EventBus`, no serialization
required. Keep payloads JSON-serializable anyway so the same shapes survive a
later move to a data channel or bus without changes.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

EventType = Literal[
    "participant.joined",
    "transcript.partial",
    "transcript.final",
    "barge_in",
    "dtmf",
    "call.ended",
]


@dataclass
class EventEnvelope:
    """Every event Person 1 emits, in one envelope.

    call_id: stable per-call key. For real calls this is the LiveKit room name
    (convention: "call-<xxxx>", set by the SIP dispatch rule); for mock calls
    it's whatever the script says.
    """

    type: EventType
    call_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    # Payload shapes by type (documented, not enforced):
    #   participant.joined: {caller_number: str, room_name: str}
    #   transcript.partial: {text: str}
    #   transcript.final:   {text: str, language: str | None}
    #   barge_in:           {} (optionally {truncated: bool})
    #   dtmf:               {digit: str}
    #   call.ended:         {reason: str}


class SpeakCommand(TypedDict):
    """Person 2 -> Person 1: make the Active Agent say `text` on the call."""

    call_id: str
    text: str
    allow_interruptions: bool


class StopSpeakingCommand(TypedDict):
    """Person 2 -> Person 1: manual stop, distinct from auto barge-in."""

    call_id: str


class DialCommand(TypedDict):
    """Person 4 -> Person 1: place ONE outbound call (sequential cascade)."""

    to_number: str
    call_id_for_correlation: str


class SendSmsCommand(TypedDict):
    """Person 4 -> Person 1: send ONE SMS.

    NOTE: the demo number is voice-only; SMS will fail until a second
    SMS-capable number exists. The cascade is voice-only for the demo.
    """

    to_number: str
    body: str
    call_id_for_correlation: str


COMMAND_TYPES = ("speak", "stop_speaking", "dial", "send_sms")
