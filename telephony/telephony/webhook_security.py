"""Twilio webhook signature validation.

Inbound voice never hits a webhook on the SIP-trunk path, so this applies to
any Twilio HTTP callback we expose later (SMS status callbacks, inbound SMS
"YES" replies once an SMS-capable number exists, video-link callbacks for M8).

Framework-agnostic core + a FastAPI dependency wrapper.
"""

from __future__ import annotations

import os

from twilio.request_validator import RequestValidator


def is_valid_twilio_request(
    url: str,
    params: dict[str, str],
    signature: str,
    auth_token: str | None = None,
) -> bool:
    """`url` must be the exact public URL Twilio signed — watch out for
    https termination / proxies rewriting the scheme or host."""
    validator = RequestValidator(auth_token or os.environ["TWILIO_AUTH_TOKEN"])
    return validator.validate(url, params, signature)


async def require_twilio_signature(request) -> None:  # FastAPI dependency
    """Usage:

        @app.post("/sms-status", dependencies=[Depends(require_twilio_signature)])
        async def sms_status(...): ...
    """
    from fastapi import HTTPException

    form = await request.form()
    signature = request.headers.get("X-Twilio-Signature", "")
    if not is_valid_twilio_request(str(request.url), dict(form), signature):
        raise HTTPException(status_code=403, detail="invalid Twilio signature")
