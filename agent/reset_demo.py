"""Reset the Supabase demo state between runs:  .venv/bin/python reset_demo.py

Gives Mrs. Patterson's shift back to Maria (status scheduled) and clears
callouts / offers / events, so the call-out scenario can run again fresh.
"""

import asyncio

import httpx

import db
from config import SUPABASE_KEY, SUPABASE_URL

HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


async def main() -> None:
    if not db.configured():
        raise SystemExit("Supabase env missing")

    marias = await db.select("caregivers", {"name": "ilike.*Maria*", "limit": "1"})
    maria = marias[0] if marias else None
    shifts = await db.select("shifts", {"client_name": "eq.Mrs. Patterson", "limit": "1"})
    if not maria or not shifts:
        raise SystemExit("Seed data missing - re-run schema.sql")
    shift_id = shifts[0]["id"]

    async with httpx.AsyncClient(timeout=15) as c:
        for table in ("offers", "callouts", "events"):
            await c.delete(f"{SUPABASE_URL}/rest/v1/{table}?shift_id=eq.{shift_id}",
                           headers=HEADERS)
    await db.update("shifts", {"id": f"eq.{shift_id}"},
                    {"status": "scheduled", "caregiver_id": maria["id"]})
    print(f"reset OK - {shifts[0]['client_name']} shift back to Maria (scheduled)")


if __name__ == "__main__":
    asyncio.run(main())
