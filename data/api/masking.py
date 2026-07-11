"""Masks PHI-adjacent fields for display/logging. Never use this on data
that needs to be dialed, texted, or matched — only on data that's about to
be printed, logged, or shown on screen.
"""


def mask_phone(phone: str) -> str:
    """+19179070164 -> +1917***0164. Keeps enough to sanity-check the
    number belongs to the right person, hides the rest.
    """
    if not phone or len(phone) < 8:
        return "***"
    return f"{phone[:5]}***{phone[-4:]}"


def mask_name(name: str) -> str:
    """Maria Alvarez -> M. A."""
    if not name:
        return "***"
    parts = name.split()
    return " ".join(f"{part[0]}." for part in parts if part)


def mask_record(record: dict) -> dict:
    """Returns a copy of a caller/caregiver/patient dict with phone and
    name masked. Use this anywhere a record is about to be logged or
    printed, not when it's being used internally to place a call.
    """
    masked = dict(record)
    if "phone" in masked:
        masked["phone"] = mask_phone(masked["phone"])
    if "name" in masked:
        masked["name"] = mask_name(masked["name"])
    return masked
