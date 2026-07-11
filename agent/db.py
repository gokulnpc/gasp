"""Async Supabase REST (httpx) - same pattern as livekit-dispatch."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config import SUPABASE_KEY, SUPABASE_URL

log = logging.getLogger("db")

_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _url(table: str) -> str:
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL not set")
    return f"{SUPABASE_URL}/rest/v1/{table}"


async def select(table: str, params: dict[str, Any]) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(_url(table), params=params, headers=_HEADERS)
        r.raise_for_status()
        return r.json()


async def insert(table: str, row: dict) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(_url(table), json=row, headers=_HEADERS)
        r.raise_for_status()
        return r.json()[0]


async def update(table: str, params: dict[str, Any], patch: dict) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.patch(_url(table), params=params, json=patch, headers=_HEADERS)
        r.raise_for_status()
        return r.json()


async def caregiver_by_phone(phone: str) -> dict | None:
    rows = await select("caregivers", {"phone": f"eq.{phone.strip()}", "limit": "1"})
    return rows[0] if rows else None


async def upcoming_shifts(caregiver_id: str) -> list[dict]:
    return await select("shifts", {
        "caregiver_id": f"eq.{caregiver_id}",
        "status": "in.(scheduled,callout,offering)",
        "order": "starts_at.asc",
        "limit": "5",
    })


async def active_caregivers() -> list[dict]:
    return await select("caregivers", {"active": "eq.true"})


async def claim_shift(shift_id: str, caregiver_id: str) -> bool:
    rows = await update(
        "shifts",
        {"id": f"eq.{shift_id}", "status": "neq.filled"},
        {"status": "filled", "caregiver_id": caregiver_id},
    )
    return bool(rows)


async def log_event(actor: str, action: str, detail: str = "",
                    shift_id: str | None = None, actor_name: str = "") -> None:
    log.info("[%s/%s] %s: %s", actor, actor_name or "-", action, detail)
    try:
        await insert("events", {
            "actor": actor, "actor_name": actor_name or None,
            "action": action, "detail": detail, "shift_id": shift_id,
        })
    except Exception as exc:
        log.warning("event insert failed (%s)", exc)
