"""Real telephony for the GASP agent: Twilio SMS + LiveKit SIP calls.

Same three functions sim.py exposes - callers don't care which one runs:
  send_sms(to, body)                 Twilio Messages API (number is SMS-capable)
  place_call(to, purpose, room)      LiveKit SIP participant via outbound trunk;
                                     our agent is dispatched into the room first
                                     so the callee hears the cascade conversation
  dial_into_room(to, room, purpose)  ring a phone INTO an existing call room
                                     (SW4 coordinator patch-in)

SIM_MODE=all (or missing keys) falls back to sim.py per action, loudly.
"""

from __future__ import annotations

import logging

import sim
from config import (AGENT_NAME, LIVEKIT_SIP_OUTBOUND_TRUNK_ID, SIM_CALLS,
                    SIM_SMS, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
                    TWILIO_VOICE_NUMBER)

log = logging.getLogger("telephony")


async def send_sms(to: str, body: str) -> dict:
    if SIM_SMS:
        return await sim.send_sms(to, body)

    import asyncio

    from twilio.rest import Client

    def _send() -> str:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        return client.messages.create(to=to, from_=TWILIO_VOICE_NUMBER, body=body).sid

    try:
        sid = await asyncio.to_thread(_send)
        log.info("SMS -> %s sid=%s", to, sid)
        return {"simulated": False, "to": to, "sid": sid}
    except Exception as exc:
        log.error("SMS -> %s FAILED: %s", to, exc)
        return {"simulated": False, "to": to, "error": str(exc)}


async def place_call(to: str, purpose: str, room_name: str | None = None,
                     metadata: str = "") -> dict:
    """Outbound cascade call: dispatch our agent into a fresh room, then dial."""
    if SIM_CALLS:
        return await sim.place_call(to, purpose)

    import uuid

    from livekit import api

    room = room_name or f"call-out-{uuid.uuid4().hex[:8]}"
    lk = api.LiveKitAPI()
    try:
        # agent first, so the callee never sits in an empty room
        await lk.agent_dispatch.create_dispatch(api.CreateAgentDispatchRequest(
            agent_name=AGENT_NAME, room=room, metadata=metadata,
        ))
        participant = await lk.sip.create_sip_participant(api.CreateSIPParticipantRequest(
            sip_trunk_id=LIVEKIT_SIP_OUTBOUND_TRUNK_ID,
            sip_call_to=to,
            sip_number=TWILIO_VOICE_NUMBER,
            room_name=room,
            participant_identity=f"phone-{to}",
            wait_until_answered=False,
        ))
        log.info("CALL -> %s room=%s (%s)", to, room, purpose)
        return {"simulated": False, "to": to, "room": room,
                "participant": participant.participant_identity}
    except Exception as exc:
        log.error("CALL -> %s FAILED: %s", to, exc)
        return {"simulated": False, "to": to, "error": str(exc)}
    finally:
        await lk.aclose()


async def dial_into_room(to: str, room_name: str, purpose: str) -> dict:
    """Patch a real phone into an ongoing call (coordinator escalation)."""
    if SIM_CALLS:
        return await sim.dial_into_room(to, room_name, purpose)

    from livekit import api

    lk = api.LiveKitAPI()
    try:
        participant = await lk.sip.create_sip_participant(api.CreateSIPParticipantRequest(
            sip_trunk_id=LIVEKIT_SIP_OUTBOUND_TRUNK_ID,
            sip_call_to=to,
            sip_number=TWILIO_VOICE_NUMBER,
            room_name=room_name,
            participant_identity=f"patch-{to}",
            wait_until_answered=False,
        ))
        log.info("PATCH -> %s into %s (%s)", to, room_name, purpose)
        return {"simulated": False, "to": to, "room": room_name,
                "participant": participant.participant_identity}
    except Exception as exc:
        log.error("PATCH -> %s FAILED: %s", to, exc)
        return {"simulated": False, "to": to, "error": str(exc)}
    finally:
        await lk.aclose()
