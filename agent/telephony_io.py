"""Real telephony via Twilio + LiveKit SIP (from gasp/telephony/outbound.py).

Same three functions cascade/override already call — sim.py delegates here
when SIM_MODE=off. Falls back to simulation_log.txt when keys are missing.
"""

from __future__ import annotations

import asyncio
import logging
import time

from config import (
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    LIVEKIT_URL,
    SIM_LOG,
    SIM_MODE,
    SIP_OUTBOUND_TRUNK_ID,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_VOICE_NUMBER,
)

log = logging.getLogger("telephony")

_sim = SIM_MODE == "all" or not (TWILIO_ACCOUNT_SID and SIP_OUTBOUND_TRUNK_ID)


def _is_fake(number: str) -> bool:
    """Seed/demo numbers (+1555..., +1000...) don't exist on the PSTN.
    Route them to the sim log so real Twilio never sees them (error 21211)."""
    return number.startswith("+1555") or number.startswith("+1000")


def _record(kind: str, line: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    entry = f"[{stamp}] {kind:9s} {line}"
    log.info("SIM %s", entry)
    with SIM_LOG.open("a") as f:
        f.write(entry + "\n")


async def send_sms(to: str, body: str) -> dict:
    """Never raises: telephony failures must not take down the voice loop."""
    if _sim or not TWILIO_ACCOUNT_SID or _is_fake(to):
        _record("SMS ->", f"{to}: {body}")
        return {"simulated": True, "to": to}

    def _send() -> str:
        from twilio.rest import Client
        msg = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN).messages.create(
            to=to, from_=TWILIO_VOICE_NUMBER, body=body,
        )
        return msg.sid

    try:
        sid = await asyncio.to_thread(_send)
    except Exception as exc:
        log.error("send_sms %s failed: %s", to, exc)
        _record("SMS FAIL", f"{to}: {exc}")
        return {"ok": False, "error": str(exc), "to": to}
    log.info("SMS -> %s sid=%s", to, sid)
    return {"ok": True, "sid": sid, "to": to}


async def place_call(to: str, purpose: str, room_name: str | None = None) -> dict:
    """Outbound voice leg into a LiveKit room (cascade offer calls)."""
    room = room_name or f"cascade-{to.replace('+', '')}"
    if _sim or _is_fake(to):
        _record("CALL ->", f"{to} room={room}: {purpose}")
        return {"simulated": True, "to": to, "room": room}

    from livekit import api

    lk = api.LiveKitAPI(url=LIVEKIT_URL, api_key=LIVEKIT_API_KEY,
                        api_secret=LIVEKIT_API_SECRET)
    try:
        participant = await lk.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=SIP_OUTBOUND_TRUNK_ID,
                sip_call_to=to,
                sip_number=TWILIO_VOICE_NUMBER,
                room_name=room,
                participant_identity=f"phone-{to}",
                wait_until_answered=False,
            )
        )
        log.info("CALL -> %s room=%s (%s)", to, room, purpose)
        return {"ok": True, "room": room, "id": participant.participant_identity}
    except Exception as exc:
        log.error("place_call %s failed: %s", to, exc)
        _record("CALL FAIL", f"{to}: {exc}")
        return {"ok": False, "error": str(exc)}
    finally:
        await lk.aclose()


async def dial_into_room(to: str, room_name: str, purpose: str) -> dict:
    """Warm-transfer: ring a phone and drop them into an ongoing call's room."""
    if not room_name or room_name == "console":
        _record("PATCH ->", f"{to} (no live room, console mode): {purpose}")
        return {"simulated": True, "to": to, "reason": "console mode"}
    return await place_call(to, purpose, room_name=room_name)
