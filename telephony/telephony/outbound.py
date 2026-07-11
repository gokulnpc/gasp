"""Outbound transport for the SW1 cascade: `dial` and `send_sms`.

Single-contact primitives ONLY (no broadcast/fan-out) — Person 4's cascade
logic loops sequentially with its own ~20-30s timeout per contact.

Per team decision, outbound voice goes through LiveKit: `dial` creates a SIP
participant that calls the contact and drops them into a LiveKit room, where
the same voice agent stack can run the "can you cover this shift?"
conversation. Requires the LiveKit *outbound* trunk (created by
scripts/setup_livekit_sip.py against the Twilio Termination URI +
credential list).

SMS caveat: the demo number (+19297307867) is VOICE-ONLY. `send_sms` is built
and contract-stable, but every send will fail until an SMS-capable number
exists — the demo cascade is voice-only.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from livekit import api
from twilio.rest import Client as TwilioClient

logger = logging.getLogger("telephony.outbound")


@dataclass
class OutboundResult:
    ok: bool
    id: str | None  # LiveKit participant identity or Twilio message SID
    error: str | None = None


class OutboundTransport:
    def __init__(
        self,
        *,
        livekit_url: str | None = None,
        livekit_api_key: str | None = None,
        livekit_api_secret: str | None = None,
        sip_outbound_trunk_id: str | None = None,
        twilio_account_sid: str | None = None,
        twilio_auth_token: str | None = None,
        voice_number: str | None = None,
    ) -> None:
        self.livekit_url = livekit_url or os.getenv("LIVEKIT_URL", "")
        self.livekit_api_key = livekit_api_key or os.getenv("LIVEKIT_API_KEY", "")
        self.livekit_api_secret = livekit_api_secret or os.getenv("LIVEKIT_API_SECRET", "")
        self.trunk_id = sip_outbound_trunk_id or os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID", "")
        self.voice_number = voice_number or os.getenv("TWILIO_VOICE_NUMBER", "")
        self._twilio = TwilioClient(
            twilio_account_sid or os.getenv("TWILIO_ACCOUNT_SID", ""),
            twilio_auth_token or os.getenv("TWILIO_AUTH_TOKEN", ""),
        )

    async def dial(self, to_number: str, room_name: str) -> OutboundResult:
        """Place ONE outbound call via LiveKit SIP (through the Twilio trunk).

        The callee lands in `room_name` as a SIP participant; dispatch the
        voice agent into that room to run the cascade conversation. Sequencing
        and the per-contact timeout are the caller's (Person 4's) job.
        """
        lk = api.LiveKitAPI(
            url=self.livekit_url,
            api_key=self.livekit_api_key,
            api_secret=self.livekit_api_secret,
        )
        try:
            participant = await lk.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=self.trunk_id,
                    sip_call_to=to_number,
                    sip_number=self.voice_number,  # outbound caller ID
                    room_name=room_name,
                    participant_identity=f"cascade-{to_number}",
                    wait_until_answered=True,
                )
            )
            logger.info("dial %s -> room %s ok", to_number, room_name)
            return OutboundResult(ok=True, id=participant.participant_identity)
        except Exception as e:  # noqa: BLE001 — contract returns errors, never raises
            logger.warning("dial %s failed: %s", to_number, e)
            return OutboundResult(ok=False, id=None, error=str(e))
        finally:
            await lk.aclose()

    def send_sms(self, to_number: str, body: str) -> OutboundResult:
        """Send ONE SMS to ONE contact.

        WILL FAIL with the current voice-only number — kept contract-stable so
        Person 4's code doesn't change when an SMS-capable number arrives.
        """
        try:
            msg = self._twilio.messages.create(
                to=to_number, from_=self.voice_number, body=body
            )
            return OutboundResult(ok=True, id=msg.sid)
        except Exception as e:  # noqa: BLE001
            logger.warning("send_sms %s failed (expected: number is voice-only): %s",
                           to_number, e)
            return OutboundResult(ok=False, id=None, error=str(e))
