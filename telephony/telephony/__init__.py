"""Person 1 · Telephony & Voice I/O for the Healthcare Omni-Agent.

Public surface for Persons 2 and 4:
  - contracts: event/command payload shapes (the Hour-0 contract, §3.7 of the plan)
  - event_bus: in-process pub/sub used to move events/commands between streams
  - mock_emitter: scripted call replay for building without live telephony
  - outbound: dial()/send_sms() single-contact primitives for the SW1 cascade
"""

from .contracts import (
    EventEnvelope,
    EventType,
    SpeakCommand,
    StopSpeakingCommand,
    DialCommand,
    SendSmsCommand,
)
from .event_bus import EventBus

__all__ = [
    "EventEnvelope",
    "EventType",
    "SpeakCommand",
    "StopSpeakingCommand",
    "DialCommand",
    "SendSmsCommand",
    "EventBus",
]
