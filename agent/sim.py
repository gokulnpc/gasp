"""Simulated telephony: SMS + outbound calls, no Twilio.

Every action prints a loud console line and lands in simulation_log.txt,
so the cascade is visible live during a demo. Same function signatures the
real Twilio/SIP layer will expose later.
"""

from __future__ import annotations

import logging
import time

from config import SIM_LOG

log = logging.getLogger("sim")


def _record(kind: str, line: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    entry = f"[{stamp}] {kind:9s} {line}"
    log.info("SIM %s", entry)
    with SIM_LOG.open("a") as f:
        f.write(entry + "\n")


async def send_sms(to: str, body: str) -> dict:
    _record("SMS ->", f"{to}: {body}")
    return {"simulated": True, "to": to}


async def place_call(to: str, purpose: str) -> dict:
    _record("CALL ->", f"{to}: {purpose}")
    return {"simulated": True, "to": to}


async def dial_into_room(to: str, room_name: str, purpose: str) -> dict:
    _record("PATCH ->", f"{to} into {room_name}: {purpose}")
    return {"simulated": True, "to": to, "room": room_name}
