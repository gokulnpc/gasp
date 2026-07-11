"""Minimal in-process pub/sub for the Person 1 <-> Person 2/4 contract.

Per the team decision, events and commands move in-process (same LiveKit agent
worker), not over Redis or an external bus. Person 2 subscribes to events with
`bus.on_event(...)`; Persons 2/4 send commands with `bus.send_command(...)`,
which Person 1's voice agent / outbound transport handles.

Both sync and async subscribers are supported; async handlers are scheduled on
the running event loop so emitting never blocks the audio path.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Awaitable, Callable

from .contracts import EventEnvelope

logger = logging.getLogger("telephony.bus")

EventHandler = Callable[[EventEnvelope], None | Awaitable[None]]
CommandHandler = Callable[[dict[str, Any]], None | Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._event_handlers: list[EventHandler] = []
        self._command_handlers: dict[str, list[CommandHandler]] = {}

    # -- events: Person 1 emits, Person 2 listens ---------------------------

    def on_event(self, handler: EventHandler) -> EventHandler:
        """Subscribe to all telephony events. Usable as a decorator."""
        self._event_handlers.append(handler)
        return handler

    def emit(self, event: EventEnvelope) -> None:
        """Fire-and-forget: never raises, never blocks the audio path."""
        logger.debug("event %s call=%s %s", event.type, event.call_id, event.payload)
        for handler in self._event_handlers:
            self._dispatch(handler, event)

    # -- commands: Person 2/4 send, Person 1 handles ------------------------

    def on_command(self, command_type: str) -> Callable[[CommandHandler], CommandHandler]:
        """Register a handler for a command type ("speak", "dial", ...)."""

        def register(handler: CommandHandler) -> CommandHandler:
            self._command_handlers.setdefault(command_type, []).append(handler)
            return handler

        return register

    def send_command(self, command_type: str, command: dict[str, Any]) -> None:
        handlers = self._command_handlers.get(command_type, [])
        if not handlers:
            logger.warning("no handler registered for command %r", command_type)
        for handler in handlers:
            self._dispatch(handler, command)

    # -- internals -----------------------------------------------------------

    @staticmethod
    def _dispatch(handler: Callable[..., Any], arg: Any) -> None:
        try:
            result = handler(arg)
            if inspect.isawaitable(result):
                asyncio.ensure_future(result)
        except Exception:
            logger.exception("handler %r failed", handler)
