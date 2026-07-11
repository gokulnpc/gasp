"""Shift-backfill cascade - runs in the dispatch worker, not on the voice call."""

from __future__ import annotations

import asyncio
import logging

import db
import sim
from config import DEMO_FAST
from data import api as data

log = logging.getLogger("cascade")

WAVE_SIZE = 2
WAVE_WAIT_S = 8 if DEMO_FAST else 45
DEMO_ACCEPT_PHONE = data.DEMO_ACCEPT_PHONE


async def run_callout(callout: dict) -> None:
    """Process one callout job: rank backups -> SMS waves -> first YES locks shift."""
    shift_id = callout["shift_id"]
    exclude = callout.get("caregiver_id")
    shift = await data.get_shift(shift_id)
    if not shift:
        log.error("missing shift %s", shift_id)
        return

    await data.update_shift(shift_id, {"status": "offering"})
    if db.configured():
        await db.log_event("worker", "cascade_started", callout.get("reason", ""),
                           shift_id=shift_id)

    backups = await data.find_backups(shift_id, exclude_id=exclude)
    if not backups:
        log.warning("no backups for shift %s", shift_id)
        return

    offer = (f"Sunrise Home Care: open shift with {shift['client_name']} "
             f"({shift['starts_at']}). Reply YES to take it.")
    filled_by = None

    for wave_i, wave_start in enumerate(range(0, len(backups), WAVE_SIZE)):
        if await data.shift_is_filled(shift_id):
            break
        wave = backups[wave_start:wave_start + WAVE_SIZE]
        log.info("wave %d -> %s", wave_i + 1, ", ".join(c["name"] for c in wave))
        for b in wave:
            await sim.send_sms(b["phone"], offer)
            if db.configured():
                await db.insert("offers", {
                    "shift_id": shift_id, "caregiver_id": b["id"],
                    "wave": wave_i + 1, "channel": "sms",
                })
        filled_by = await _await_yes(shift_id, wave)
        if filled_by:
            break

    if filled_by:
        log.info("shift %s FILLED by %s", shift_id, filled_by["name"])
        if db.configured():
            await db.log_event("worker", "shift_filled", filled_by["name"],
                               shift_id=shift_id, actor_name=filled_by["name"])
        for b in backups:
            if b["id"] != filled_by["id"]:
                await sim.send_sms(b["phone"], "Shift filled - thanks anyway!")
        await sim.send_sms(filled_by["phone"],
                           f"Confirmed: {shift['client_name']} shift is yours.")
    else:
        log.warning("cascade exhausted for shift %s", shift_id)
        if db.configured():
            await db.log_event("worker", "cascade_exhausted", shift_id=shift_id)


async def _await_yes(shift_id: str, wave: list[dict]) -> dict | None:
    """Simulated reply: demo caregiver (James / +15550002) says YES after a few seconds."""
    responder = next((b for b in wave if b["phone"] == DEMO_ACCEPT_PHONE), None)
    if not responder:
        await asyncio.sleep(WAVE_WAIT_S)
        return None
    await asyncio.sleep(4 if DEMO_FAST else 15)
    if await data.try_lock_shift(shift_id, responder["id"]):
        return responder
    return None
