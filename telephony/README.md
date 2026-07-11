# Person 1 · Telephony & Voice I/O

Implements the plan in [`../docs/person1-implementation-plan.md`](../docs/person1-implementation-plan.md): the telephony spine (M0), the voice half of the Dual-Agent core with barge-in (M1), and the outbound transport for the SW1 cascade.

## Layout

| File | What it is |
|---|---|
| `telephony/contracts.py` | The Hour-0 event/command contract (payload shapes) shared with Persons 2/4 |
| `telephony/event_bus.py` | In-process pub/sub carrying events/commands (team decision: no Redis) |
| `telephony/mock_emitter.py` | **Day-0 deliverable** — scripted call replay; Persons 2/4 build against this |
| `telephony/voice_agent.py` | LiveKit agent: ElevenLabs STT/TTS, recording disclosure, barge-in events |
| `telephony/outbound.py` | `dial()` (LiveKit SIP participant) + `send_sms()` (Twilio) — single-contact, sequential cascade |
| `telephony/webhook_security.py` | Twilio webhook signature validation |
| `scripts/setup_livekit_sip.py` | One-time LiveKit inbound/outbound trunk + dispatch rule setup |

## Setup

```bash
cd gasp/telephony
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in keys (LiveKit creds come from Person 2)
```

## Run

```bash
# Day-0 mock (no phone/keys needed) — what Persons 2/4 integrate against:
python -m telephony.mock_emitter

# One-time LiveKit SIP resources (after .env is filled):
python scripts/setup_livekit_sip.py

# The live voice agent (echo mode = self-test without Person 2's brain):
GASP_ECHO_MODE=1 python -m telephony.voice_agent dev
```

Then call **+1 (929) 730-7867** — Twilio trunk `Arya-Hack` originates to `sip:5bwxm1tai7w.sip.livekit.cloud`, the dispatch rule drops the caller into a `call-*` room, and the agent answers with the recording disclosure.

## Contract (for Persons 2 & 4)

Events out (subscribe via `bus.on_event`): `participant.joined`, `transcript.partial`, `transcript.final`, `barge_in`, `dtmf`, `call.ended` — all as `EventEnvelope(type, call_id, payload, ts)`.

Commands in (send via `bus.send_command(type, dict)`): `speak{call_id, text, allow_interruptions}`, `stop_speaking{call_id}`, `dial{to_number, call_id_for_correlation}`, `send_sms{to_number, body, call_id_for_correlation}`.

`call_id` == LiveKit room name (`call-<xxxx>`).

## Known constraints

- The Twilio number is **voice-only** — `send_sms` fails until an SMS-capable number exists; the SW1 cascade is voice-only for the demo.
- Language is defaulted to English; Spanish voice/STT is wired but the detection mechanism (DTMF vs profile) is an open team decision.
- SW4 conferencing and M8 (video link) are deferred per the plan.
