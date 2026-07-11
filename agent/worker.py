"""Dispatch worker - picks up callout jobs from Supabase and runs the cascade.

Run in a second terminal while the voice agent is live:
  python worker.py

The voice agent ONLY inserts a callout row; this process does the rescheduling
(SMS waves, first-YES-wins shift lock). Same split as livekit-dispatch.
"""

from __future__ import annotations

import asyncio
import logging

import cascade
import db
from config import DEMO_FAST, startup_report

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)-11s %(levelname)-7s %(message)s",
                    datefmt="%H:%M:%S")
logging.getLogger("httpx").setLevel(logging.WARNING)  # hide idle-poll noise
log = logging.getLogger("worker")

POLL_SECONDS = 3 if DEMO_FAST else 5


async def claim(callout_id: str) -> bool:
    rows = await db.update("callouts",
                           {"id": f"eq.{callout_id}", "processed": "eq.false"},
                           {"processed": True})
    return bool(rows)


async def handle(callout: dict) -> None:
    if not await claim(callout["id"]):
        return
    log.info("picked up callout %s (shift %s)", callout["id"], callout["shift_id"])
    try:
        await cascade.run_callout(callout)
    except Exception:
        log.exception("cascade failed for callout %s", callout["id"])


async def poll_loop() -> None:
    while True:
        try:
            pending = await db.select("callouts", {
                "processed": "eq.false",
                "order": "created_at.asc",
            })
            for callout in pending:
                asyncio.create_task(handle(callout))
        except Exception as exc:
            log.warning("poll failed: %s", exc)
        await asyncio.sleep(POLL_SECONDS)


async def main() -> None:
    if not db.configured():
        raise SystemExit("SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY required for worker")
    print("GASP dispatch worker\n" + startup_report())
    await poll_loop()


if __name__ == "__main__":
    asyncio.run(main())
