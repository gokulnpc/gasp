# Person 1 Implementation Plan · Telephony & Voice I/O

_Purpose: a reviewable plan (not code) for Person 1's slice of the Healthcare Omni-Agent build — telephony transport, voice I/O, barge-in, outbound cascade transport, the mock event emitter, and webhook security. Read this before writing any real code; corrections belong here first._
_Owner: Person 1 · Status: Draft — pending user review_

> **Scope guardrail.** This document plans Person 1's stream ONLY: Twilio↔LiveKit transport, ElevenLabs voice I/O, barge-in signaling, outbound `dial`/`send_sms`, webhook security, and the mock event emitter. Person 2's Orchestrator/Passive Agent, Person 3's Neo4j/data layer, and Person 4's SubWorkflow business logic are referenced only at the contract boundary — where Person 1's code emits an event or accepts a command.

---

## 1. Overview

Person 1 owns the telephony spine and voice I/O for the Healthcare Omni-Agent — the shared foundation every other stream builds on, per [`09-work-split.md`](./09-work-split.md): milestone **M0 (Telephony spine)**, the **voice half of M1 (Dual-Agent core + barge-in)**, and the **M8 stretch (Twilio Video link)**. This plan makes one deliberate deviation from the written docs (`05-integrations.md`'s "Media Streams WebSocket" description): instead of Twilio streaming raw audio to a custom WebSocket server, we use **Twilio Elastic SIP Trunking → LiveKit's SIP endpoint**, so an inbound caller becomes a native LiveKit room participant. This is an upgrade, not a replacement of intent — it still satisfies FR-1/FR-3 and the M0/M1 deliverables, but hands audio transport to LiveKit's SFU and lets Person 2's Orchestrator (built on LiveKit) attach as another room participant/agent rather than consuming a bespoke WebSocket protocol. Voice I/O runs through LiveKit Agents' ElevenLabs plugin (STT+TTS, or speech-to-speech if available) as the primary path, with a direct ElevenLabs WebSocket integration flagged as a fallback only if the plugin can't hit the required latency/interruption bar. Everything here is scoped to reliability for a live, rehearsable demo over cleverness.

---

## 2. Action items / decisions needed before coding

**Status: confirmed by user on 2026-07-11 — see §2.1 for locked config, resolved items struck through below.**

| # | Item | Detail | Status |
|---|---|---|---|
| A | ~~Twilio number has Voice only, no SMS/MMS~~ | **Resolved (accepted constraint, not blocking):** no second number will be provisioned right now (Twilio verification/process takes too long for the demo window). **SW1's cascade runs voice-only for the demo** — no SMS leg. Revisit post-hackathon if time allows. | Closed |
| B | ~~SIP trunk vs alternative — confirm with Person 2~~ | **Resolved:** Person 2 confirmed they are building on **LiveKit**. Twilio Elastic SIP Trunking → LiveKit SIP endpoint is the locked approach. | Closed |
| C | **LiveKit ElevenLabs plugin latency/interruption check** | Still open — spike this early in the build (see §5, step 2). ElevenLabs account (10K credits, via teammate) is available to test against. | Open — build-time task |
| D | ~~Account-level prerequisites~~ | **Resolved:** user has Twilio Console access and can grant access as needed. ElevenLabs account available. Elastic SIP Trunk already created — see §2.1. LiveKit project is Person 2's; get SIP host from them (see §2.1, Origination). | Mostly closed — pending LiveKit SIP host from Person 2 |

### 2.1 Locked Twilio trunk config (as of 2026-07-11)

| Item | Value |
|---|---|
| Elastic SIP Trunk SID | `TK21e8a9e33f9963c6ce2255b049e8cce0` |
| Trunk friendly name | `Arya-Hack` |
| Twilio number attached | `+19297307867` ((929) 730-7867) — Voice only, no SMS/MMS |
| Termination SIP URI | Set to a chosen prefix (e.g. `arya-hack` → `arya-hack.pstn.twilio.com`) + a Credential List (username/password) attached under Authentication. Used later as the `address`/`auth_username`/`auth_password` for LiveKit's **outbound** trunk, if/when outbound cascade calls are routed through LiveKit instead of plain TwiML. |
| Origination URI | `sip:5bwxm1tai7w.sip.livekit.cloud` — obtained from Person 2's LiveKit project (Settings → Project → SIP URI). Added under Origination → Origination URI, priority/weight at default `10`/`10`. |
| Event/command transport | In-process within the LiveKit agent worker (or direct calls across agents in the same room/process) — **not** Redis or an external message bus, per Person 2. |

---

## 3. Component breakdown

> **Caveat (applies to every snippet in this section):** All code below is illustrative, pseudocode-level, and **not verified against current SDK versions** of `twilio`, `livekit-agents`, `livekit-api`, or the ElevenLabs SDK/plugin. Method names, constructor signatures, and plugin class names WILL drift — check current docs for `twilio` (Python), `livekit-agents`, `livekit-api`, and the LiveKit ElevenLabs plugin before running any of this.

### 3.1 Twilio SIP trunk configuration

Mostly **console/API config, not application code** — this happens once per environment, not per-call.

Step-by-step:
1. In Twilio Console → **Elastic SIP Trunking**, create a trunk (or do it via API/Terraform-less script below).
2. Set the trunk's **Origination URL**(s) to point at LiveKit's SIP URI for your project (LiveKit gives you a SIP endpoint like `sip:<project>.sip.livekit.cloud` — get this from LiveKit Console → SIP, after enabling SIP on the project).
3. Associate your Voice-capable phone number with the trunk (Console: Trunk → Numbers → add existing number, or via API).
4. Configure the trunk's Termination URI / auth (IP ACL or credential list) per LiveKit's SIP trunk requirements — LiveKit Cloud SIP typically wants either IP allowlisting Twilio's SIP signaling IPs, or trunk-level username/password auth that matches a LiveKit inbound trunk config.
5. Test with Twilio's trunk validation (Console has a "test call" / debugger tool) before wiring anything else.

```python
# Illustrative only — verify against current `twilio` SDK docs before running.
from twilio.rest import Client

client = Client(account_sid, auth_token)

trunk = client.trunking.v1.trunks.create(friendly_name="gasp-livekit-trunk")

trunk.origination_urls.create(
    friendly_name="livekit-sip",
    sip_url="sip:<your-project>.sip.livekit.cloud",  # from LiveKit SIP console
    weight=10,
    priority=10,
    enabled=True,
)

# Attach the existing Twilio number (voice-only) to this trunk.
trunk.phone_numbers.create(phone_number_sid=EXISTING_VOICE_NUMBER_SID)
```

### 3.2 LiveKit SIP dispatch rule / inbound trunk config

Half CLI/console config (creating the inbound trunk + dispatch rule resources), half code if you script it via `livekit-api`. Recommend doing this via the **LiveKit CLI** (`lk sip inbound create`, `lk sip dispatch create` — exact subcommands may differ by CLI version) for a first pass, and only scripting it in `livekit-api` if you need to recreate it repeatedly (e.g. CI, multi-env).

```python
# Illustrative only — verify against current `livekit-api` docs/method names before running.
from livekit import api

lk = api.LiveKitAPI(url=LIVEKIT_URL, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)

# 1. Register an inbound SIP trunk resource that matches numbers from Twilio.
inbound_trunk = await lk.sip.create_sip_inbound_trunk(
    api.CreateSIPInboundTrunkRequest(
        trunk=api.SIPInboundTrunk(
            name="gasp-inbound",
            numbers=["+1XXXXXXXXXX"],  # the Twilio voice number
        )
    )
)

# 2. Dispatch rule: route inbound SIP calls into a room, one room per call.
dispatch_rule = await lk.sip.create_sip_dispatch_rule(
    api.CreateSIPDispatchRuleRequest(
        rule=api.SIPDispatchRule(
            dispatch_rule_individual=api.SIPDispatchRuleIndividual(
                room_prefix="call-",  # room name = call-<random>, agreed with Person 2
            )
        ),
        trunk_ids=[inbound_trunk.sip_trunk_id],
    )
)
```

**Contract note for Hour 0:** agree the room-naming convention (`call-<call_sid>` recommended, since Twilio's `CallSid` is a stable unique key) so Person 2's Orchestrator agent can be **dispatched into the same room automatically** (LiveKit agent dispatch by room name pattern) rather than needing an out-of-band signal.

### 3.3 LiveKit Agent wired to ElevenLabs (voice I/O)

This is Person 1's core deliverable: a `livekit-agents` worker that joins the room, speaks the recording-disclosure prompt, and runs STT/TTS through ElevenLabs.

```python
# Illustrative only — verify against current `livekit-agents` + ElevenLabs plugin docs.
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import elevenlabs, silero  # exact plugin names/module paths may differ

RECORDING_DISCLOSURE_EN = (
    "This call may be recorded for quality and training purposes."
)
RECORDING_DISCLOSURE_ES = (
    "Esta llamada puede ser grabada con fines de calidad y capacitacion."
)

class VoiceIOAgent(Agent):
    def __init__(self, language: str = "en"):
        super().__init__(
            instructions="You are a phone assistant for a home-health agency.",
            stt=elevenlabs.STT(language=language),       # or a partner STT plugin if EL STT plugin is unavailable
            tts=elevenlabs.TTS(voice_id=VOICE_ID_BY_LANG[language]),
            vad=silero.VAD.load(),                         # turn/endpoint + interruption detection
        )

async def entrypoint(ctx):
    await ctx.connect()
    language = detect_language_from_dtmf_or_default(ctx)  # simple heuristic; real intent detection is Person 2's
    session = AgentSession()
    await session.start(
        agent=VoiceIOAgent(language=language),
        room=ctx.room,
        room_input_options=RoomInputOptions(),  # e.g. noise cancellation if available
    )
    disclosure = RECORDING_DISCLOSURE_EN if language == "en" else RECORDING_DISCLOSURE_ES
    await session.say(disclosure, allow_interruptions=False)  # spoken before anything else
    # From here, session handles turns; emit events per the contract in §3.7.
```

**Fallback path (flagged, not primary):** if the plugin's turn-detection/interruption latency doesn't meet the ≲1s / "near-instant barge-in" bar from `06-non-functional-requirements.md`, fall back to a direct ElevenLabs WebSocket speech-to-speech session, publishing/subscribing raw audio frames to/from a LiveKit audio track manually. This is materially more code (manual audio framing, resampling, and interruption logic) — only take this path after the Hour-0-adjacent latency spike (§2.C) shows the plugin path is insufficient.

### 3.4 Barge-in / interruption handling

LiveKit Agents' built-in VAD + interruption handling (via the `vad=` param above and the agent session's turn-detection) already does "stop TTS playback when the user starts speaking" out of the box in most configurations. Person 1's job is to make sure that moment also emits a `barge_in` event onto the contract so Person 2's Passive Agent can snapshot/resume state.

```python
# Illustrative only — verify against current AgentSession event API.
@session.on("user_started_speaking")
def _on_user_started_speaking():
    # LiveKit's agent session already stops/cancels the in-flight TTS generation.
    emit_event(EventEnvelope(
        type="barge_in",
        call_id=call_id,
        payload={},
    ))

@session.on("agent_speech_interrupted")
def _on_agent_speech_interrupted(info):
    # Optional: richer signal with how much of the utterance was spoken, if the SDK exposes it.
    emit_event(EventEnvelope(type="barge_in", call_id=call_id, payload={"truncated_text": info.text}))
```

The "snapshot state, resume" logic itself lives in Person 2's Passive Agent — Person 1's contract obligation is only to **emit `barge_in` reliably and promptly** the moment playback stops, and to not swallow or buffer that event.

### 3.5 Outbound transport (`dial` / `send_sms`)

A small module Person 4's SW1 cascade logic calls one contact at a time (per the sequential cascade decision — this module intentionally does NOT support broadcast/fan-out; it exposes single-contact primitives and lets the caller loop with its own timeout).

```python
# Illustrative only — verify against current `twilio` Python SDK docs.
from twilio.rest import Client
from dataclasses import dataclass

@dataclass
class OutboundResult:
    ok: bool
    sid: str | None
    error: str | None = None

class OutboundTransport:
    def __init__(self, account_sid: str, auth_token: str, voice_number: str, sms_number: str):
        self.client = Client(account_sid, auth_token)
        self.voice_number = voice_number
        self.sms_number = sms_number  # CAVEAT: separate number until the SMS-capability gap (Action Item A) is resolved

    def dial(self, to_number: str, twiml_url: str) -> OutboundResult:
        """Places ONE outbound call. Caller (SW1 cascade logic) is responsible for
        sequencing single contacts with its own ~20-30s timeout before moving to the next."""
        try:
            call = self.client.calls.create(to=to_number, from_=self.voice_number, url=twiml_url)
            return OutboundResult(ok=True, sid=call.sid)
        except Exception as e:
            return OutboundResult(ok=False, sid=None, error=str(e))

    def send_sms(self, to_number: str, body: str) -> OutboundResult:
        """Places ONE outbound SMS to ONE contact — no batch/broadcast helper by design,
        to match the sequential cascade strategy."""
        try:
            msg = self.client.messages.create(to=to_number, from_=self.sms_number, body=body)
            return OutboundResult(ok=True, sid=msg.sid)
        except Exception as e:
            return OutboundResult(ok=False, sid=None, error=str(e))
```

Note: `dial()` here is a plain PSTN call via `twilio.rest.Client.calls.create`, separate from the SIP-trunked inbound path — outbound cascade calls don't need to land in a LiveKit room (they're closer to a simple TTS playback / IVR "are you available?" call), unless the team wants the *same* voice agent to run the outbound leg too, in which case it should also be dialed into a LiveKit room via a SIP participant (`create_sip_participant`) rather than plain TwiML. **Flagging this as a design choice to confirm** — see Open Questions.

### 3.6 Webhook signature validation (Twilio)

Applies to any Twilio webhook Person 1's code exposes (SMS status callbacks, inbound SMS replies for the cascade's "YES", trunk-related status callbacks if any — inbound *voice* itself bypasses this once fully on the SIP trunk path, since there's no per-call Twilio voice webhook to validate).

```python
# Illustrative only — verify against current `twilio` SDK validator API.
from twilio.request_validator import RequestValidator
from functools import wraps
from flask import request, abort  # or FastAPI equivalent — adjust to actual framework choice

validator = RequestValidator(TWILIO_AUTH_TOKEN)

def require_twilio_signature(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        signature = request.headers.get("X-Twilio-Signature", "")
        url = request.url  # must exactly match the URL Twilio signed (watch proxies/https termination)
        if not validator.validate(url, request.form, signature):
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped
```

### 3.7 The Hour-0 event/command contract, re-expressed for LiveKit

`09-work-split.md`'s Hour-0 contract was written for a raw-Twilio-webhook world. Re-expressed for LiveKit-room-as-transport:

| Old (docs) | New (LiveKit world) | Direction | Notes |
|---|---|---|---|
| `call.started{callerNumber}` | `participant.joined{caller_number, call_id, room_name}` | Person 1 → Person 2 | Fires when the SIP participant appears in the room; `call_id` = Twilio `CallSid` if available via SIP headers, else room name |
| `user.utterance{text}` | `transcript.final{text, call_id}` (+ optional `transcript.partial{text}` for interim) | Person 1 → Person 2 | From STT plugin's transcript events |
| `barge_in` | `barge_in{call_id}` | Person 1 → Person 2 | See §3.4 |
| `dtmf` | `dtmf{digit, call_id}` | Person 1 → Person 2 | From LiveKit SIP DTMF events, if used for language selection |
| `call.ended` | `call.ended{call_id, reason}` | Person 1 → Person 2 | Room/participant disconnect |
| `speak(text)` | `speak(text, call_id, allow_interruptions=True)` | Person 2 → Person 1 | Person 2 tells Active Agent what to say (e.g. after SW logic decides a response) |
| `stop_speaking()` | `stop_speaking(call_id)` | Person 2 → Person 1 | Manual override, distinct from auto barge-in |
| `dial(number)` | `dial(number, call_id_for_correlation)` | Person 4 (via Person 2 or directly) → Person 1 | See §3.5 |
| `send_sms(to,body)` | `send_sms(to, body, call_id_for_correlation)` | Person 4 (via Person 2 or directly) → Person 1 | See §3.5 |
| `start_conference(legs)` | `start_conference(legs, call_id)` | Person 4/2 → Person 1 | For SW4 escalation; still TBD whether this is a Twilio conference or a LiveKit room merge (see Open Questions) |

```python
# Illustrative only — sketch of the shared payload shapes. Actual transport (in-process
# pub/sub, Redis, a LiveKit data channel, or plain function calls) is a Hour-0 decision
# with Person 2, not fixed here.
from dataclasses import dataclass, field
from typing import Literal, TypedDict, Any

EventType = Literal[
    "participant.joined", "transcript.final", "transcript.partial",
    "barge_in", "dtmf", "call.ended",
]

@dataclass
class EventEnvelope:
    type: EventType
    call_id: str
    payload: dict[str, Any] = field(default_factory=dict)

class SpeakCommand(TypedDict):
    call_id: str
    text: str
    allow_interruptions: bool

class DialCommand(TypedDict):
    call_id_for_correlation: str
    to_number: str

class SendSmsCommand(TypedDict):
    call_id_for_correlation: str
    to_number: str
    body: str
```

### 3.8 The mock event emitter (Day-0 deliverable)

Unblocks Person 2 and Person 4 before any real phone/LiveKit room exists. Replays a scripted sequence of the events from §3.7 with realistic delays, and accepts (logs) the inbound commands so downstream code can be built/tested against it without touching Twilio or LiveKit.

```python
# Illustrative only — a Day-0 unblocker, not production code.
import asyncio
import time
from dataclasses import asdict

class MockCallEmitter:
    """Replays a scripted call as a sequence of EventEnvelope-shaped dicts with delays,
    and logs/echoes any commands sent back in (speak/stop_speaking/dial/send_sms/etc.)
    so Persons 2 and 4 can build against the contract before real telephony exists."""

    def __init__(self, script: list[tuple[float, dict]], on_event=print):
        self.script = script          # [(delay_seconds, event_dict), ...]
        self.on_event = on_event
        self.commands_received: list[dict] = []

    async def run(self):
        for delay, event in self.script:
            await asyncio.sleep(delay)
            self.on_event(event)

    def receive_command(self, command: dict):
        """Call this from Person 2/4's code in place of a real `speak`/`dial`/`send_sms` call."""
        self.commands_received.append({**command, "_received_at": time.time()})
        print(f"[mock] received command: {command}")


DEFAULT_CALLOUT_SCRIPT = [
    (0.0, {"type": "participant.joined", "call_id": "mock-call-1",
           "payload": {"caller_number": "+15551234567", "room_name": "call-mock-call-1"}}),
    (1.5, {"type": "transcript.final", "call_id": "mock-call-1",
           "payload": {"text": "Hi, this is Maria, I can't make my shift today."}}),
    (4.0, {"type": "barge_in", "call_id": "mock-call-1", "payload": {}}),
    (4.2, {"type": "transcript.final", "call_id": "mock-call-1",
           "payload": {"text": "Actually wait, it's for tomorrow's shift, not today."}}),
    (9.0, {"type": "call.ended", "call_id": "mock-call-1", "payload": {"reason": "caller_hangup"}}),
]

if __name__ == "__main__":
    emitter = MockCallEmitter(DEFAULT_CALLOUT_SCRIPT)
    asyncio.run(emitter.run())
```

Deliver this **before** any real Twilio/LiveKit wiring is attempted — it is the thing that keeps Persons 2 and 4 unblocked, per `09-work-split.md`'s "mock-first" philosophy.

---

## 4. Demo-day reliability notes

The demo is judged live; a clever-but-fragile path is worse than a boring-but-solid one.

- **LiveKit SIP trunk drops mid-demo:** have a **direct dial-in backup number** (a second, simpler Twilio number wired straight to TwiML `<Say>`/`<Gather>` with no LiveKit/agent dependency) that can narrate a canned fallback ("we're experiencing a technical issue, here's what would happen next...") if the primary path fails live. Rehearse switching to it.
- **ElevenLabs slow/down:** keep a **pre-recorded audio fallback** (a handful of MP3s covering the demo script's key lines, in English and Spanish) that can be played via Twilio `<Play>` or a LiveKit audio file track if the live TTS call times out or errors. Wrap every ElevenLabs call with a timeout + fallback-to-recording path, not a silent failure.
- **Barge-in mis-fires or feels sluggish live:** rehearse the exact interrupt line/timing beforehand; if VAD sensitivity is flaky, consider a manual "kill switch" (e.g. a DTMF key or a keyword) that force-triggers `stop_speaking()` so the demo moment is reliable even if auto-detection isn't perfectly tuned by demo time.
- **Cascade outbound call/SMS fails (carrier delay, bad number):** demo with a **known-good pre-registered backup number** (e.g. a team member's phone) rather than a real caregiver number, and have a manual "fake the YES" path (a pre-staged inbound SMS/call) ready in case live carrier delivery is slow on stage Wi-Fi/cell.
- **End-to-end test protocol before the demo:** (1) test the SIP trunk with a real inbound call from an outside phone, not just a softphone/simulator; (2) test on the actual venue network if possible — conference Wi-Fi is a common failure point for real-time voice; (3) rehearse the full demo script (`07-roadmap-execution-plan.md`'s demo script) at least twice, timing the barge-in moment; (4) have a **recorded video of a successful run** as an absolute last-resort fallback if live telephony fails entirely on stage.

---

## 5. Sequenced build order for Person 1 only

1. **Accounts & keys.** Confirm Twilio SIP trunking + LiveKit SIP are enabled; get all API keys/IDs into `.env` (never commit).
2. **Latency spike (timeboxed, ~2-3 hrs).** Stand up the LiveKit Agent + ElevenLabs plugin in isolation (no Twilio yet — use LiveKit's own test room/token) and measure time-to-first-audio and interruption responsiveness against the NFR targets. Go/no-go on the plugin path vs the WebSocket fallback (Action Item C).
3. **Mock event emitter (Day 0 deliverable).** Ship §3.8 first so Persons 2 and 4 are unblocked immediately, independent of how the spike in step 2 resolves.
4. **Twilio SIP trunk + LiveKit inbound trunk/dispatch rule wiring.** Get one real inbound call landing a caller as a LiveKit room participant end-to-end (no agent logic yet — just prove connectivity).
5. **Voice I/O agent (M0).** Wire the LiveKit Agent from §3.3 into that room: recording disclosure, streaming STT/TTS, basic echo/response loop.
6. **Barge-in wiring (voice-half of M1).** Confirm auto-interrupt behavior and emit `barge_in` reliably (§3.4); test against a real caller talking over playback.
7. **Event/command contract implementation (§3.7).** Replace the mock emitter's direct calls with the real event bus wired to the live agent, keeping the exact same payload shapes so Persons 2/4's code doesn't need to change.
8. **Outbound transport (`dial`/`send_sms`).** Build and test §3.5 against the (possibly second) SMS-capable number once Action Item A is resolved.
9. **Webhook signature validation.** Add to any exposed webhook endpoints (SMS status/inbound-reply callbacks) before anything is demo-exposed publicly.
10. **Conferencing/line-patch stub for SW4.** Coordinate with Person 4 on whether escalation uses a Twilio conference leg or a LiveKit room merge (open question below); build a minimal version.
11. **(Stretch, M8) Twilio Video link for visual validation** — only after 1-10 are solid.
12. **Demo hardening pass** — implement the fallbacks in §4, rehearse end-to-end.
13. **Hand off to Person 4 for integration** — freeze the event/command contract, document any deviations from §3.7 that emerged during build, and pair with Person 4 on wiring real telephony into the live SubWorkflow demo.

---

## 6. Open questions — status as of 2026-07-11

| Question | Status |
|---|---|
| SMS number choice | **Resolved:** no second number for now; SW1 cascade is voice-only for the demo. |
| Outbound cascade calls — same LiveKit agent or plain TwiML? | **Resolved:** outbound is via **LiveKit** (SIP participant into a room), not plain TwiML — consistent with the inbound path. |
| SW4 conferencing mechanism | **Deferred, not blocking.** SW4 is a stretch milestone (M7), shared with Person 4; not a decision Person 1 needs to make now. Revisit once M0/M1 are solid. |
| Room-naming/dispatch convention with Person 2 | Still open — confirm `call-<CallSid>` convention directly with Person 2 when wiring the dispatch rule. |
| Event contract transport mechanism | **Resolved:** in-process within the LiveKit agent worker, not Redis/a message bus. |
| Language detection mechanism | Still open — decide DTMF vs. heuristic vs. profile lookup with Person 2 before building the language-select step. |
| Recording-disclosure wording | **Resolved:** generic EN/ES placeholder wording in §3.3 is good enough as-is. |
| Separate outbound caller-ID number for cascade | **Resolved:** the existing number (`+19297307867`) doubles as outbound caller ID; no separate number needed. |

### Remaining blocker before build can fully start

**None.** LiveKit SIP host (`sip:5bwxm1tai7w.sip.livekit.cloud`) obtained and added to the Origination tab — see §2.1. Trunk (`Arya-Hack` / `TK21e8a9e33f9963c6ce2255b049e8cce0`) is fully configured: Numbers, Termination (SIP URI + credential list), and Origination all set. Cleared to start build per §5.
