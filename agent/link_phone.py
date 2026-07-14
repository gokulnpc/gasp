"""Map a REAL phone number to a seeded caregiver so identify_caller works
when you call from your own cell:

    .venv/bin/python link_phone.py +19295614558 Maria
    .venv/bin/python link_phone.py --list
"""

import asyncio
import sys

import db


async def main() -> None:
    if not db.configured():
        raise SystemExit("Supabase env missing")

    if "--list" in sys.argv:
        for cg in await db.select("caregivers", {"select": "name,phone", "order": "name"}):
            print(f"  {cg['name']:<15} {cg['phone']}")
        return

    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    phone, name = sys.argv[1], sys.argv[2]

    rows = await db.select("caregivers", {"name": f"ilike.*{name}*", "limit": "2"})
    if len(rows) != 1:
        raise SystemExit(f"need exactly one caregiver matching {name!r}, got {len(rows)}")
    caregiver = rows[0]

    # Free the number if another caregiver holds it (unique constraint)
    taken = await db.select("caregivers", {"phone": f"eq.{phone}"})
    for other in taken:
        if other["id"] != caregiver["id"]:
            await db.update("caregivers", {"id": f"eq.{other['id']}"},
                            {"phone": f"+1000{other['id'][:7]}"})
            print(f"freed {phone} from {other['name']}")

    await db.update("caregivers", {"id": f"eq.{caregiver['id']}"}, {"phone": phone})
    print(f"OK: {caregiver['name']} now answers to {phone}")


if __name__ == "__main__":
    asyncio.run(main())
