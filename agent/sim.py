"""Simulated telephony — delegates to telephony_io when SIM_MODE=off."""

from __future__ import annotations

import telephony_io as _real


async def send_sms(to: str, body: str) -> dict:
    return await _real.send_sms(to, body)


async def place_call(to: str, purpose: str) -> dict:
    return await _real.place_call(to, purpose)


async def dial_into_room(to: str, room_name: str, purpose: str) -> dict:
    return await _real.dial_into_room(to, room_name, purpose)
