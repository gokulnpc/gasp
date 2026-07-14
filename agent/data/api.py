"""Data facade: Supabase when configured, in-memory seed otherwise.

Voice agent + worker both call this module. Callouts are the job queue:
SW1 inserts a row -> worker picks it up -> cascade runs off the call.
"""

from __future__ import annotations

import asyncio
import copy
import logging
import time
from typing import Any, Optional

import db
from . import seed

log = logging.getLogger("data")

_use_db = db.configured()
_db_live: bool | None = None
_caregivers = copy.deepcopy(seed.CAREGIVERS)
_shifts = copy.deepcopy(seed.SHIFTS)
AUDIT_LOG: list[dict[str, Any]] = []
_shift_locks: dict[str, str] = {}
_lock = asyncio.Lock()

# Demo: James accepts first (phone matches livekit-dispatch seed)
DEMO_ACCEPT_PHONE = "+15550002"


def using_supabase() -> bool:
    return _use_db and _db_live is not False


async def _db_ready() -> bool:
    """True when Supabase is configured AND schema tables exist."""
    global _db_live
    if not _use_db:
        return False
    if _db_live is not None:
        return _db_live
    try:
        await db.select("caregivers", {"limit": "1"})
        _db_live = True
        log.info("Supabase connected (caregivers table OK)")
    except Exception as exc:
        _db_live = False
        log.warning("Supabase tables missing? Run schema.sql — using seed fallback (%s)", exc)
    return _db_live


def _fmt_shift(s: dict) -> dict:
    return {
        "id": s["id"],
        "shift_id": s["id"],
        "client_name": s.get("client_name", s.get("client", "")),
        "caregiver_id": s.get("caregiver_id"),
        "starts_at": str(s.get("starts_at", "")),
        "ends_at": str(s.get("ends_at", "")),
        "status": s.get("status", ""),
        "required_skills": s.get("required_skills", []),
    }


def _fmt_caregiver(c: dict) -> dict:
    skills = c.get("skills") or c.get("certifications") or []
    return {
        "id": c["id"],
        "name": c["name"],
        "phone": c["phone"],
        "languages": c.get("languages", ["english"]),
        "certifications": list(skills),
        "skills": list(skills),
        "reliability": c.get("reliability", 0.9),
    }


async def get_caller_by_phone(phone: str) -> Optional[dict[str, Any]]:
    if await _db_ready():
        row = await db.caregiver_by_phone(phone)
        return _fmt_caregiver(row) if row else None
    for cg in _caregivers.values():
        if cg["phone"] == phone:
            return dict(cg)
    return None


async def get_caller_by_name(name: str) -> Optional[dict[str, Any]]:
    """Fuzzy caregiver lookup for callers whose number we don't recognize.
    Tries the full name, then each word ('Maria, New York' still finds
    Maria Lopez). Returns the single best match or None if ambiguous."""
    tokens = [t.strip(" ,.").lower() for t in name.split() if len(t.strip(" ,.")) > 2]
    candidates = [name.strip().lower()] + tokens
    if await _db_ready():
        for cand in candidates:
            try:
                rows = await db.select(
                    "caregivers",
                    {"name": f"ilike.*{cand}*", "active": "eq.true", "limit": "2"},
                )
            except Exception as exc:
                log.warning("name lookup failed: %s", exc)
                return None
            if len(rows) == 1:
                return _fmt_caregiver(rows[0])
        return None
    for cand in candidates:
        hits = [cg for cg in _caregivers.values() if cand in cg["name"].lower()]
        if len(hits) == 1:
            return dict(hits[0])
    return None


async def upcoming_shifts(caregiver_id: str) -> list[dict[str, Any]]:
    if await _db_ready():
        return [_fmt_shift(s) for s in await db.upcoming_shifts(caregiver_id)]
    open_status = ("scheduled", "callout", "offering", "SCHEDULED", "OPEN")
    return [_fmt_shift(s) for s in _shifts.values()
            if s["caregiver_id"] == caregiver_id and s["status"] in open_status]


async def get_shift(shift_id: str) -> Optional[dict[str, Any]]:
    if await _db_ready():
        try:
            rows = await db.select("shifts", {"id": f"eq.{shift_id}", "limit": "1"})
        except Exception:
            # LLM sometimes passes junk ("the ten AM shift") - not a uuid.
            # Postgres rejects it; treat as not-found so callers can recover.
            return None
        return _fmt_shift(rows[0]) if rows else None
    s = _shifts.get(shift_id)
    return _fmt_shift(s) if s else None


async def resolve_shift(shift_ref: str, caregiver_id: str | None) -> Optional[dict[str, Any]]:
    """Resolve a spoken shift reference to a real row. Exact id first, then
    fuzzy match on the caregiver's upcoming shifts by client name; if they
    have exactly one open shift, that's the one they mean."""
    shift = await get_shift(shift_ref)
    if shift:
        return shift
    if not caregiver_id:
        return None
    shifts = await upcoming_shifts(caregiver_id)
    if len(shifts) == 1:
        return shifts[0]
    ref = shift_ref.lower()
    matches = [s for s in shifts
               if s["client_name"] and s["client_name"].lower().split()[-1] in ref]
    return matches[0] if len(matches) == 1 else None


async def update_shift(shift_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    if await _db_ready():
        rows = await db.update("shifts", {"id": f"eq.{shift_id}"}, patch)
        return _fmt_shift(rows[0]) if rows else {}
    _shifts[shift_id].update(patch)
    return _fmt_shift(_shifts[shift_id])


async def create_callout(shift_id: str, caregiver_id: str, reason: str) -> dict[str, Any]:
    """Insert a callout job for the dispatch worker."""
    if not await _db_ready():
        raise RuntimeError("Supabase not ready — run schema.sql in Supabase SQL Editor first")
    await db.update("shifts", {"id": f"eq.{shift_id}"}, {"status": "callout"})
    row = await db.insert("callouts", {
        "shift_id": shift_id,
        "caregiver_id": caregiver_id,
        "reason": reason,
        "channel": "voice",
    })
    await db.log_event("sw1", "callout_received", reason, shift_id=shift_id)
    return row


async def find_backups(shift_id: str, exclude_id: str | None = None) -> list[dict[str, Any]]:
    if await _db_ready():
        shift = await get_shift(shift_id)
        if not shift:
            return []
        needed = set(shift.get("required_skills") or [])
        ranked = []
        for cg in await db.active_caregivers():
            if exclude_id and cg["id"] == exclude_id:
                continue
            skills = set(cg.get("skills") or [])
            overlap = len(needed & skills) if needed else 1
            ranked.append((overlap * 2 + cg.get("reliability", 0), cg))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [_fmt_caregiver(c) for _, c in ranked[:4]]
    ids = seed.BACKUPS.get(shift_id, [])
    out = [_fmt_caregiver(_caregivers[i]) for i in ids if i in _caregivers]
    if exclude_id:
        out = [c for c in out if c["id"] != exclude_id]
    return out


async def match_caregivers(patient_profile: dict[str, Any]) -> list[dict[str, Any]]:
    langs = {l.lower() for l in patient_profile.get("languages", [])}
    zip_ = str(patient_profile.get("zip", ""))[:3]

    def score(cg: dict) -> float:
        lang_hit = len(langs & {l.lower() for l in cg.get("languages", ["english"])})
        zip_hit = 1.0 if str(cg.get("home_zip", ""))[:3] == zip_ else 0.0
        certs = cg.get("certifications") or cg.get("skills") or []
        return lang_hit * 3 + len(certs) + zip_hit * 2 + cg.get("reliability", 0.9)

    if await _db_ready():
        cgs = [_fmt_caregiver(c) for c in await db.active_caregivers()]
    else:
        cgs = [dict(c) for c in _caregivers.values()]
    ranked = sorted(cgs, key=score, reverse=True)
    return [c | {"match_score": round(score(c), 2)} for c in ranked[:3]]


async def get_med_layout(patient_id: str) -> list[dict[str, Any]]:
    """Mocked med layouts; unknown/missing patient falls back to the default demo layout."""
    layout = seed.MED_LAYOUTS.get(patient_id) or seed.MED_LAYOUTS["pt-chen"]
    return [dict(m) for m in layout]


async def append_audit_log(entry: dict[str, Any]) -> dict[str, Any]:
    if await _db_ready():
        action = entry.get("type", "audit")
        detail = ", ".join(f"{k}={v}" for k, v in entry.items() if k != "type")
        await db.log_event("gasp", action, detail, shift_id=entry.get("shift_id"))
        return entry
    record = {"ts": time.time(), **entry}
    AUDIT_LOG.append(record)
    log.info("AUDIT + %s", entry)
    return record


async def try_lock_shift(shift_id: str, caregiver_id: str) -> bool:
    if await _db_ready():
        return await db.claim_shift(shift_id, caregiver_id)
    async with _lock:
        if shift_id in _shift_locks:
            return False
        _shift_locks[shift_id] = caregiver_id
        _shifts[shift_id]["status"] = "filled"
        _shifts[shift_id]["caregiver_id"] = caregiver_id
        return True


async def shift_is_filled(shift_id: str) -> bool:
    s = await get_shift(shift_id)
    return bool(s) and s.get("status") == "filled"
